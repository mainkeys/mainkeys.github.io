---
title: 能调用 TA 之前，系统是怎样启动起来的？
date: "2026-09-18T03:20:09+08:00"
tags: [Secure Boot, TF-A, ARMv8, OP-TEE, TEE]
categories: [系统安全]
description: 回到第一次 TEE 调用之前，分别梳理 TF-A 的执行交接和镜像认证关系，并沿固定版本源码追到认证失败的出口。
series: 顺着一次 TEE 调用
series_order: 6
permalink: /post/tee-06-before-the-first-call.html
---

前面几篇一直沿着一次 CA 请求往里走，但偷偷借用了一个前提：Linux 已经启动，OP-TEE 也已经在那儿等着。现在把时间往前拨一点，问题就变了。这些代码是谁放进内存的？CPU 先执行谁？如果加载进来的是一份被改过的镜像，到底在哪一步会停下来？

光看 BL1、BL2、BL31、BL32、BL33，我很容易把它们背成一串编号。背下来以后能顺着念，却还是回答不了“BL31 是不是负责验 BL32”。所以这篇画两条线：一条看执行权交给谁，另一条看谁凭什么被接受。两条线放到一起理解，但箭头的意思一定写清楚。

## 先锁住这次看的版本

本系列选择 OP-TEE manifest 4.10.0，实际提交为 `6d5849d5c1e4054980bf430ce1e96ebd0f532590`。它的 [qemu_v8.xml](https://github.com/OP-TEE/manifest/blob/6d5849d5c1e4054980bf430ce1e96ebd0f532590/qemu_v8.xml) 指定 TF-A v2.14.0，对应提交 `1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc`。下文 TF-A 源码链接全部指向这个提交，不把今天的主分支悄悄当作同一个版本。

配置也要一起看。本次[实验任务 35257180558](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558) 已通过，归档的 [build-config.txt](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/build-config.txt) 明确记录 `TF_A_TRUSTED_BOARD_BOOT=n`。固定 OP-TEE build 的 [qemu_v8.mk](https://github.com/OP-TEE/build/blob/53bfd321ee7fd47e450fb88c04b08ea27819f9bc/qemu_v8.mk) 只有在它为 `y` 时才添加 `TRUSTED_BOARD_BOOT=1` 和 `GENERATE_COT=1`。这次启动和 hello_world 调用都成功了，但没有验证 TBB；后文的认证失败分析依赖固定源码。

## 从上电走到 Linux，谁在执行

本文采用 AArch64、QEMU virt、传统 `SPD=opteed` 的部署来读代码。TF-A 中 BL1 做早期工作并加载 BL2；BL2 继续装载后续阶段并准备入口信息；执行权随后交给 EL3 的 BL31。BL31 初始化运行时服务，并通过 dispatcher 初始化作为 BL32 的 OP-TEE；OP-TEE 完成这部分初始化后把控制权交回，BL31 再进入普通世界的 BL33。本配置把 U-Boot 作为 BL33，由它继续引导 Linux。[TF-A Firmware Design](https://trustedfirmware-a.readthedocs.io/en/v2.14.0/design/firmware-design.html) 说明了各阶段职责和可替换方案。

![启动执行顺序与镜像认证关系分别示意](/post/tee-06-before-the-first-call/architecture.svg)

| 阶段 | 这次配置中的角色 | 后面还会不会见到它 |
| --- | --- | --- |
| BL1 | 早期固件、进入 BL2 前的准备 | 参与经典 BL2 到 BL31 的交接 |
| BL2 | 装载并准备后续镜像 | 完成交接后不作为日常 TEE 调用入口 |
| BL31 | EL3 运行时固件 | Linux 运行后仍处理相应固件服务 |
| BL32 | OP-TEE 安全负载 | 后续 CA 请求需要它处理 |
| BL33 | U-Boot 普通世界启动软件 | 继续进入 Linux 引导流程 |

图里的 BL32 不是所有 TF-A 系统的必选项，BL33 也不天然等于 Linux。TF-A 支持由其他早期固件提供相应阶段，还有 BL2 运行在 EL3 等不同路径。这里先固定一条线，才能知道自己正在看哪个入口；换平台时，不能用这张图反过来要求厂商实现必须长得一样。

另一个细节是，BL32 常常不等于一个单独的完整文件。这个 build 配置会分别传入 OP-TEE header、pager 和 pageable 对应的 `BL32`、`BL32_EXTRA1`、`BL32_EXTRA2`。如果只拿一个叫 `bl32.bin` 的文件名讨论认证范围，很可能把其他被加载的数据遗漏掉。

本次[普通世界 UART](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-normal.txt) 已经把启动过程留下来了。下面按原顺序摘录，省略号表示删去的行，保留了一条稍后要解释的警告：

```text
NOTICE:  BL1: v2.14.0(release):1d5aa93
...
WARNING: Firmware Image Package header check failed.
NOTICE:  BL1: Booting BL2
NOTICE:  BL2: v2.14.0(release):1d5aa93
...
NOTICE:  BL1: Booting BL31
NOTICE:  BL31: v2.14.0(release):1d5aa93
...
U-Boot 2025.07-ge37de002fac3 (Sep 17 2026 - 18:14:15 +0000)
...
Welcome to Buildroot, type root or test to login
```

[安全世界 UART](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-secure.txt) 另有 `Primary CPU initializing` 和 `Primary CPU switching to normal world boot`，以及 OP-TEE 提交 `753afbb` 的版本信息。两份记录对应不同串口；它们支持上述启动阶段已经执行，不能拼成逐指令的跨世界时间线。

看到 FIP 警告，我先对照了 [io_fip.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/drivers/io/io_fip.c)：读取头成功后，若 `name` 不等于 `TOC_HEADER_NAME`，或 `serial_number` 为零，就打印这句话并返回 `-ENOENT`。它检查的是容器头结构，没有执行签名认证。

[QEMU IO 策略](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/plat/qemu/common/qemu_io_storage.c) 先尝试内存映射的 FIP，失败后可按镜像 ID 转向 semihosting 文件读取。这次命令使用 `-bios bl1.bin` 并开启 semihosting，与该备用路径相容。不过日志没有逐次输出所选镜像和读到的头字段，不能把五条警告分别归到某个镜像，更不能据此断言镜像被篡改。能确定的是：出现了结构检查警告，系统随后继续启动。

## 装进内存和允许执行，是两个判断

启动装载需要解决的是“从哪里读、放到哪里、大小合不合适”。镜像认证需要解决的是“这些字节是否属于被授权接受的内容”。一份文件能被读取、尺寸也正确，只说明前一类条件可能满足；名字叫 `trusted`，同样不能代替后一类判断。

TF-A 的 Trusted Board Boot 使用信任链描述认证依赖。可以从受信任的根公钥或其哈希出发，经证书建立后续密钥与镜像摘要的可信关系，再校验实际镜像。信任根为什么值得相信，则需要平台提供保护机制；它不能只因为和镜像放在同一个可替换目录里，就自己证明自己可靠。[TF-A v2.14.0 的 TBB 设计说明](https://trustedfirmware-a.readthedocs.io/en/v2.14.0/design/trusted-board-boot.html) 讨论了这层关系。

这也是 QEMU 教学配置和真实芯片实现需要分开的地方。启用 TBB 时，固定版本的 [QEMU 平台构建规则](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/plat/qemu/qemu/platform.mk) 会准备根密钥与公钥哈希，并把相关数据纳入构建；[qemu_trusted_boot.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/plat/qemu/common/qemu_trusted_boot.c) 返回该根公钥哈希。它帮助理解软件接口，不等于已经验证某颗芯片的 OTP、熔丝或量产注入流程。

对我来说，追信任根时最该问的不是哈希算法叫什么，而是谁能改这份参考值、在什么时候能改、改完以后谁会发现。这些问题属于平台和生命周期约束，不能从一次模拟器演示里自动获得答案。

## 认证关系不是 BL31 验 BL32、BL32 再验 BL33

固定版本的 [tbbr_cot_bl2.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/drivers/auth/tbbr/tbbr_cot_bl2.c) 里有认证描述符。BL31 的父节点指向 SoC firmware content certificate，BL32 指向 trusted OS firmware content certificate，BL33 指向 non-trusted firmware content certificate。镜像节点使用摘要认证，相关证书还有自己的上级和签名认证关系。

这里的 `parent` 是认证依赖，不是“上一段执行的程序”。BL2 可以在执行权交给 BL31 之前，完成需要它装载的镜像认证；BL31 随后初始化 BL32，也不意味着这是 BL31 才开始验 BL32 的证据。执行图中看似挨着的两块，在认证图里可能位于不同分支。

同理，BL33 叫 non-trusted firmware，是在区分它的安全域和角色，不是在宣布它一定不用认证。进入普通世界以后还需不需要校验 Linux、根文件系统或其他内容，又是后续启动软件的职责。TF-A 接受了 BL33，不能替后面所有被加载的字节签一张无限期通行证。

## 验证失败到底从哪里出去

我这次最想追清楚的是失败分支。只找到一个验签函数，还不足以说“失败阻止启动”；还得确认错误有没有向上传递，调用方有没有继续跳转。

在 [common/bl_common.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/common/bl_common.c) 中，开启 TBB 且没有动态关闭认证时，装载函数进入递归认证路径：先处理认证父节点，再加载当前镜像，调用 `auth_mod_verify_img()`。认证不通过会清零该镜像内存、刷新对应缓存，并返回 `-EAUTH`。公共包装层还留有尝试其他镜像实例的机制，因此不能把通用代码描述成所有平台遇到第一个错误都立即停机。

接着看 [bl2_image_load_v2.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/bl2/bl2_image_load_v2.c)。`bl2_load_images()` 调用装载认证接口；得到非零错误后，转入 `plat_error_handler()`。默认实现在 [plat_bl_common.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/plat/common/plat_bl_common.c)，是带不返回约定的循环，在循环里执行 `wfi()`。我检索了同一提交下 QEMU 平台的 C 和汇编源，没有发现该 handler 的平台覆盖。

为了以后复查，我把函数之间的错误传递整理成下面这条阅读路线：

```text
BL2 遍历待加载镜像
  → load_auth_image
    → 启用认证时，递归处理父节点并验证当前镜像
    → 当前镜像认证失败：清零镜像，返回 -EAUTH
  → 错误未恢复：plat_error_handler
    → 默认 handler 不返回，不继续交接下一阶段
```

现在才能把结论说完整：如果开启 TBB，并满足上述认证条件，认证错误沿装载路径传回 BL2，并进入不返回的错误处理；这为“拒绝继续启动”提供了源码依据。它没有说明模拟器屏幕一定显示哪几行，也没有替真实板卡上的复位、恢复模式或看门狗策略作保证。

## 最后还要区分三件事

签名或认证通过，说明内容符合相应密钥和策略的授权条件；它不保证代码没有漏洞。旧版本可以带着合法签名，所以防回滚需要额外的版本约束与可信状态。度量启动又是在记录状态供后续判断，不能因为看到了哈希记录，就认定系统拒绝执行了不被接受的镜像。这三件事经常在同一套启动系统里合作，但不能互相代替。

TA 自己的签名检查也有另一层边界。运行期从 REE 文件系统取回的 TA，由 OP-TEE 检查和加载；这与 TF-A 启动阶段接纳 OP-TEE 固件相关，却不是同一轮文件读取或同一个验证入口。第五篇的 RPC 解决“怎样把文件送回来”，这篇的启动链解释“负责后续检查的安全内核怎样被建立起来”。

启动记录可以和[实际 manifest](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/repo-manifest.resolved.xml)、[产物摘要](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/binary-sha256.txt) 一起复查；本次[运行脚本固定在 113865db](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/run-qemu.py)。TBB 篡改测试仍未进行。若以后补做，需要显式打开认证、记录基线，再修改指定镜像并观察失败出口；本篇的源码结论不能提前替代那份实验结果。

第一季走到这里，一次 TA 调用终于有了前后关系：前面由启动软件建立运行环境，运行时经过用户态、内核、固件和安全内核，后面再把结果传回 CA。我接下来想补的驱动、可信存储和升级知识，都可以接到这些具体边界上，而不用重新收藏一堆彼此不认识的名词。

本篇图和控制流摘要为自行整理；引用的 TF-A 源文件保留上游 BSD-3-Clause 许可，本文不转载整段实现。后续如提取或修改上游代码，应同时保留原始版权和许可证声明。

系列目录：[01 CA 到 TA](/post/tee-01-ca-to-ta.html) · [02 异常级](/post/tee-02-armv8-exception-levels.html) · [03 Linux 驱动](/post/tee-03-linux-tee-driver.html) · [04 共享内存](/post/tee-04-shared-memory.html) · [05 RPC](/post/tee-05-rpc-and-supplicant.html) · **06 启动**

上一篇：[TA 还没执行完，为什么又回到了 Linux？](/post/tee-05-rpc-and-supplicant.html)　后续选题：驱动并发与内存管理、设备树、RPMB 与可信存储、安全升级和防回滚。
