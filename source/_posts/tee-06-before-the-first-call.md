---
title: 能调用 TA 之前，系统是怎样启动起来的？
date: "2026-09-13T08:00:00+08:00"
updated: "2026-09-19T08:30:00+08:00"
tags: [Secure Boot, TF-A, ARMv8, OP-TEE, TEE]
categories: [系统安全]
description: 回到第一次 TEE 调用之前，分别梳理 TF-A 的执行交接和镜像认证关系，并沿固定版本源码追到认证失败的出口。
series: 顺着一次 TEE 调用
series_order: 6
permalink: /post/tee-06-before-the-first-call.html
---

前面追 CA 调用时，Linux 和 OP-TEE 都已经完成初始化。往前看启动日志，又会遇到一组问题：谁把这些镜像放进内存，谁把控制权交给它们，加载的内容又由谁检查？

我读 TF-A 时容易混淆的是 BL31 和 BL32 的关系。BL31 会初始化作为 BL32 的 OP-TEE，但这能否说明 BL32 由 BL31 认证？沿代码查下去，执行交接和镜像认证有各自的路径，需要分开看。

## 版本和 TBB 开关

本系列使用 OP-TEE manifest 4.10.0，提交为 `6d5849d5c1e4054980bf430ce1e96ebd0f532590`。其中 [qemu_v8.xml](https://github.com/OP-TEE/manifest/blob/6d5849d5c1e4054980bf430ce1e96ebd0f532590/qemu_v8.xml) 指定 TF-A v2.14.0，对应提交 `1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc`。下文 TF-A 源码链接均固定到这一提交。

[实验记录 35257180558](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558) 对应的 [build-config.txt](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/build-config.txt) 中有一个需要留意的选项：`TF_A_TRUSTED_BOARD_BOOT=n`。固定 OP-TEE build 的 [qemu_v8.mk](https://github.com/OP-TEE/build/blob/53bfd321ee7fd47e450fb88c04b08ea27819f9bc/qemu_v8.mk) 只有在它为 `y` 时才添加 `TRUSTED_BOARD_BOOT=1` 和 `GENERATE_COT=1`。因此，启动和 hello_world 成功是本次的实测结果，TBB 认证失败的处理则只核对了源码。

## BL1 到 Linux 的执行顺序

在这套 AArch64、QEMU virt、传统 `SPD=opteed` 配置中，BL1 完成早期工作并加载 BL2。BL2 装载后续镜像、准备入口信息，执行权随后交给 EL3 的 BL31。

BL31 初始化运行时服务，通过 dispatcher 进入作为 BL32 的 OP-TEE。OP-TEE 完成初始化并交回控制权后，BL31 进入普通世界的 BL33。本次 BL33 是 U-Boot，由它继续引导 Linux。[TF-A Firmware Design](https://trustedfirmware-a.readthedocs.io/en/v2.14.0/design/firmware-design.html) 有各阶段的职责说明。

![启动执行顺序与镜像认证关系分别示意](/post/tee-06-before-the-first-call/architecture.svg)

| 阶段 | 这次配置中的角色 | 后面还会不会见到它 |
| --- | --- | --- |
| BL1 | 早期固件、进入 BL2 前的准备 | 参与经典 BL2 到 BL31 的交接 |
| BL2 | 装载并准备后续镜像 | 完成交接后不作为日常 TEE 调用入口 |
| BL31 | EL3 运行时固件 | Linux 运行后仍处理相应固件服务 |
| BL32 | OP-TEE 安全负载 | 后续 CA 请求需要它处理 |
| BL33 | U-Boot 普通世界启动软件 | 继续进入 Linux 引导流程 |

图里的 BL32 是 TF-A 的可选阶段，BL33 也可以采用其他普通世界启动软件。TF-A 还支持由其他早期固件提供相应阶段，以及 BL2 运行在 EL3 等路径。换平台读代码时，要按实际构建选项确认这几处。

这次的 BL32 还涉及多个文件。build 配置分别传入 OP-TEE header、pager 和 pageable，对应 `BL32`、`BL32_EXTRA1`、`BL32_EXTRA2`。检查装载或认证范围时，这几部分都要核对，只看 `bl32.bin` 容易漏掉其他数据。

下面是本次[普通世界 UART](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-normal.txt) 的启动摘录，顺序与原记录一致，省略号表示删去的行：

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

[安全世界 UART](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-secure.txt) 中有 `Primary CPU initializing`、`Primary CPU switching to normal world boot`，以及 OP-TEE 提交 `753afbb` 的版本信息。两份记录能用来检查启动阶段，但来自不同串口，无法据此排列每一条跨世界指令的执行时间。

日志里的 FIP 警告需要单独查一下。我在 [io_fip.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/drivers/io/io_fip.c) 中找到它的触发条件：读取头成功后，若 `name` 不等于 `TOC_HEADER_NAME`，或 `serial_number` 为零，就打印这句话并返回 `-ENOENT`。这里检查容器头结构，没有执行签名认证。

[QEMU IO 策略](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/plat/qemu/common/qemu_io_storage.c) 会尝试内存映射的 FIP，失败后可按镜像 ID 转向 semihosting 文件读取。这次命令使用 `-bios bl1.bin` 并开启 semihosting，与该备用路径相容。日志里共有五条警告，之后系统继续启动；由于没有逐次输出所选镜像和头字段，我无法把每条警告对应到具体镜像，也没有据此判断镜像被篡改的依据。

## 装载和认证分别检查什么

装载代码要确定镜像从哪里读、放到哪里，以及大小是否合适。认证代码则检查这些字节是否符合授权条件。文件可以正常读取，尺寸也正确，仍然可能在认证阶段被拒绝。文件名或阶段名中的 `trusted` 不提供这种保证。

TF-A 的 Trusted Board Boot 使用信任链描述认证依赖。从受信任的根公钥或其哈希出发，经证书取得后续密钥和镜像摘要，再校验实际镜像。根公钥或参考哈希需要平台保护；如果攻击者能同时替换镜像和这份参考值，后续检查就失去了可信依据。[TF-A v2.14.0 的 TBB 设计说明](https://trustedfirmware-a.readthedocs.io/en/v2.14.0/design/trusted-board-boot.html) 讨论了这层关系。

启用 TBB 时，固定版本的 [QEMU 平台构建规则](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/plat/qemu/qemu/platform.mk) 会准备根密钥与公钥哈希，并把相关数据纳入构建；[qemu_trusted_boot.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/plat/qemu/common/qemu_trusted_boot.c) 返回该根公钥哈希。这套实现可以用来读懂软件接口。真实芯片上还要检查 OTP、熔丝或其他存储的保护方式，以及密钥注入流程，这些不在本次实验范围内。

继续追信任根，就得查参考值在什么阶段写入、谁有权修改、是否允许再次写入。答案取决于平台和生命周期状态，单看哈希算法或 QEMU 中的取值函数还不够。

## 认证描述符里的 `parent`

认证关系可以从固定版本的 [tbbr_cot_bl2.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/drivers/auth/tbbr/tbbr_cot_bl2.c) 查起。BL31 的父节点指向 SoC firmware content certificate，BL32 指向 trusted OS firmware content certificate，BL33 指向 non-trusted firmware content certificate。镜像节点使用摘要认证，相关证书还有各自的上级和签名认证关系。

`parent` 指向当前节点依赖的认证材料。BL2 可以在执行权交给 BL31 之前，完成所装载镜像的认证。等到 BL31 初始化 BL32 时，已经走到了后面的执行交接阶段。这也回答了开头的问题：仅凭 BL31 启动 BL32 的顺序，无法判断认证由谁完成。

BL33 名称中的 non-trusted 表示它所属的安全域和角色，上面的认证描述符仍然包含它。BL33 之后加载的 Linux、根文件系统等内容，则要由后续启动软件按各自策略校验。TF-A 对 BL33 的认证范围不会自动延伸到这些内容。

## 认证失败如何传回 BL2

找到认证函数以后，我继续查了它返回错误时的调用路径。要确认失败能阻止启动，需要看到调用者收到错误后如何处理。

在 [common/bl_common.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/common/bl_common.c) 中，TBB 开启且没有动态关闭认证时，装载函数会递归处理认证父节点，加载当前镜像并调用 `auth_mod_verify_img()`。认证失败会清零该镜像内存、刷新对应缓存，返回 `-EAUTH`。公共包装层还支持尝试其他镜像实例，因此某次验证返回错误后，仍要继续检查调用方是否重试。

[bl2_image_load_v2.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/bl2/bl2_image_load_v2.c) 中的 `bl2_load_images()` 调用装载认证接口，得到非零错误后进入 `plat_error_handler()`。默认实现在 [plat_bl_common.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/plat/common/plat_bl_common.c)：函数不返回，在循环中执行 `wfi()`。我检索了同一提交下 QEMU 平台的 C 和汇编源，没有找到该 handler 的平台覆盖。

这几处函数的关系如下，图中的分支依据源码整理：

```text
BL2 遍历待加载镜像
  → load_auth_image
    → 启用认证时，递归处理父节点并验证当前镜像
    → 当前镜像认证失败：清零镜像，返回 -EAUTH
  → 错误未恢复：plat_error_handler
    → 默认 handler 不返回，不继续交接下一阶段
```

如果开启 TBB，并满足上述认证条件，未恢复的认证错误会沿装载路径传回 BL2，进入不返回的错误处理。这是本次源码核对得到的失败出口。实际板卡可能另外实现复位、恢复模式或看门狗策略，需要再查平台代码；本次也没有运行认证失败用例来观察屏幕输出。

## 认证、防回滚和度量启动

认证通过，说明内容满足相应密钥和策略的授权条件，代码本身仍可能有漏洞。旧版本也可以带着合法签名，所以防回滚还需要版本约束与可信状态。度量启动负责记录状态，供后续判断；单凭一份哈希记录，无法知道启动代码是否会拒绝某个镜像。

运行期 TA 文件的签名检查由 OP-TEE 完成。开启 TBB 时，TF-A 对 OP-TEE 固件的认证发生在启动阶段；第五篇通过 RPC 取回的 TA 文件，则交给已经运行起来的安全内核检查和加载。两个阶段相关，但使用的文件和验证入口各不相同。

复查本次启动时，可以同时看[实际 manifest](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/repo-manifest.resolved.xml)、[产物摘要](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/binary-sha256.txt) 和固定在 113865db 的[运行脚本](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/run-qemu.py)。TBB 篡改测试尚未进行；补做时需要打开认证，记录正常启动基线，再修改指定镜像、观察失败出口。这份结果要与本文的源码分析另行记录。

图和控制流摘要为自行整理。引用的 TF-A 源文件采用 BSD-3-Clause 许可，提取或修改上游代码时应保留原始版权和许可证声明。

系列目录：[01 CA 到 TA](/post/tee-01-ca-to-ta.html) · [02 异常级](/post/tee-02-armv8-exception-levels.html) · [03 Linux 驱动](/post/tee-03-linux-tee-driver.html) · [04 共享内存](/post/tee-04-shared-memory.html) · [05 RPC](/post/tee-05-rpc-and-supplicant.html) · **06 启动**

上一篇：[TA 还没执行完，为什么又回到了 Linux？](/post/tee-05-rpc-and-supplicant.html)

继续阅读：[TA 没返回，Linux 线程在等什么？](/post/linux-tee-wait-and-wakeup.html) · [镜像签名没问题，为什么还要一车一授权？](/post/vehicle-authorization-nonce-avb.html)
