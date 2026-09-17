---
title: 看 TEE 代码之前，我先把 ARMv8 的异常级理清了
date: "2026-09-18T03:20:05+08:00"
tags: [ARMv8, TrustZone, TEE, OP-TEE]
categories: [系统安全]
description: 把异常级、安全状态和执行状态拆开，再沿着一次 OP-TEE 请求看 SMC、ERET 和上下文切换各自负责什么。
series: 顺着一次 TEE 调用
series_order: 2
permalink: /post/tee-02-armv8-exception-levels.html
---

上一篇把 CA 到 TA 的路线串了一遍。继续往下看，马上会碰到几个很容易混在一起的词：EL0、EL1、EL3、Secure World、Monitor。要是只记住“数字越大权限越高”，再加一句“TEE 更安全”，脑子里大概会长出一条从 Linux 到 TA 的升级路线。

但这样想有个问题：普通用户 TA 在 S-EL0，Linux 内核在 NS-EL1。难道内核数字更大，就能直接读 TA 的内存？显然不能这么比较。我想先把这个疑问弄明白，再看汇编，否则函数名记住了一堆，图还是画不对。

## 先给一段代码标上三个坐标

Exception Level 描述异常级，影响指令、系统寄存器和特权操作；Security state 描述安全状态，参与访问隔离；Execution state 则区分 AArch64 与 AArch32。它们有关联，但不能压成同一个“权限等级”。本文只讨论传统 TrustZone 两个安全状态、AArch64 的 OP-TEE 部署，不展开 Realm，也不展开虚拟化后的异常路由。概念依据是 [Arm 的 AArch64 Exception Model，第 2、3 章](https://documentation-service.arm.com/static/63a065c41d698c4dc521cb1c)。

我给本系列画的图是下面这样。这里的 S 和 NS 分别表示 Secure、Non-secure；EL3 承担安全状态之间的管理，不需要再给它画两套彼此独立的 Monitor。

![传统 SMC 部署中的异常级与安全状态](/post/tee-02-armv8-exception-levels/architecture.svg)

| 本系列中的代码 | 所在位置 | 它直接负责的事情 |
| --- | --- | --- |
| CA、libteec、tee-supplicant | NS-EL0 | 用户态业务、客户端封装和普通世界服务 |
| Linux 内核、TEE 驱动 | NS-EL1 | 内核接口、参数转换和与固件通信 |
| TF-A BL31、opteed | EL3 | 固件服务分发及安全上下文交接 |
| OP-TEE core、pseudo TA | S-EL1 | 安全内核及其中的特权服务 |
| 用户 TA | S-EL0 | 经安全内核管理的应用代码 |

这张表是具体部署的职责安排，不是 Arm 强制所有软件照着摆。比如不能从表里推导出“Linux 永远只能运行在 EL1”。本次归档的 [build-config.txt](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/build-config.txt) 确认了 `SPMC_AT_EL=n`、`SPD=opteed`，以及普通世界和安全世界的用户、内核四侧均为 64 位：`COMPILE_NS_USER`、`COMPILE_NS_KERNEL`、`COMPILE_S_USER`、`COMPILE_S_KERNEL` 都是 `64`。这些参数与固定版本 [qemu_v8.mk](https://github.com/OP-TEE/build/blob/53bfd321ee7fd47e450fb88c04b08ea27819f9bc/qemu_v8.mk) 的传统 SMC 分支对应。

实际启动命令还选了 QEMU `virt` 机器、`virtualization=false` 和 `-cpu max,sme=on,pauth-impdef=on`。这里的 `max` 按模拟器支持情况启用处理器特性；[固定 QEMU 源码](https://github.com/qemu/qemu/blob/7c949c53e936aa3a658d84ab53bae5cadaa5d59c/target/arm/tcg/cpu64.c) 也特意让它区别于真实 CPU 型号。因此，这套实验可以帮助理解 AArch64 的执行关系，但不是对某颗 Armv8.0 芯片的精确仿真。

这也解释了为什么图里没让请求依次经过 EL0、EL1、EL2、EL3。异常级不是楼梯，不要求每层踩一脚。另一方面，某些 Armv8 扩展确实支持 Secure EL2；FF-A/SPM 的部署又有其他组合，不能把“这次不用”写成“架构不存在”。

## 在 Linux 里已经是 root，为什么还过不去

Linux 的 root 身份和 CPU 的安全状态不是一个概念。root 可以让进程获得更多 Linux 权限，但进程运行用户代码时仍然处在用户态；进入内核后，当前执行也不会因此变成 Secure。给普通世界程序提权，不能直接把一次 Non-secure 内存访问改成 Secure 访问。

反过来看，TA 在 Secure World，也不等于它能随便改 OP-TEE 的页表和内核数据。用户 TA 仍受安全内核建立的映射与权限约束。对我来说，这个区分很实用：排查问题时，要分别问“当前代码能操作哪些处理器资源”和“这次访问属于哪个安全状态”，不能只问谁的名字更像管理员。

如果把问题缩小成一个指针就更清楚了。CA 传入的地址先属于它自己的进程地址空间；驱动和 OP-TEE 需要按协议处理缓冲区，TA 最后看到的地址不能仅凭数值相同就认定是同一映射。第四篇会具体追这个过程，这里先记住：切换执行位置没有顺便统一所有人的地址空间。

## SMC 做的第一件事，并不是执行 TA

CA 调用 `TEEC_InvokeCommand()` 时，首先还是在执行普通的用户态 C 代码。经过系统调用进入内核后，OP-TEE 驱动才会走到与固件通信的位置。在本系列配置下，SMC 引发到 EL3 的异常，随后由 TF-A 分发；它不包含“直接跳到某个 TA 的 C 函数”这层业务含义。

固定 TF-A v2.14.0 的 [opteed_main.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/services/spd/opteed/opteed_main.c) 给了一个很具体的入口：`opteed_smc_handler()`。普通世界发来的合法 OP-TEE 调用会选择对应的安全入口，准备安全上下文，再交给 EL3 的退出路径。这里能看到 fast 与 yielding 入口的区分，但还看不到 hello_world 的 command 实现，因为那属于更后面的 TEE 调用协议。

我把几个层次分开记：SMC 是异常机制；SMC Function ID 用于约定固件服务；OP-TEE 消息说明要开会话还是发命令；TA 的 command ID 才选择应用操作。UUID 又是在标识目标 TA。它们解决的问题不同，不能都叫“调用号”以后就随手混用。

还得给“SMC 到 EL3”加上条件。架构允许高一级软件配置陷入控制，SMC 也不是 EL0 程序可以直接拿来调用 TEE 的用户态接口。这篇的路线建立在没有相关虚拟化拦截的传统部署上；换成虚拟机里的客户端，就得先重新确认异常到哪里去了。

## ERET 为什么能进入另一边

SMC 负责引发异常，`ERET` 负责异常返回。Monitor 用异常返回进入 OP-TEE 时，“返回”这个名字容易让我以为它要回到刚才那条 SMC 后面。但异常返回使用的是软件准备好的返回上下文，它并不理解“刚才那个调用者”的业务身份。

几个寄存器的分工可以先记到够用：`ELR_EL3` 给出返回地址，`SPSR_EL3` 提供返回时恢复的处理器状态，在本篇的两种安全状态模型下，`SCR_EL3.NS` 参与选择低异常级的安全状态。设置这些状态，再执行 `ERET`，才构成向目标环境交接的一部分；还需要正确的栈、映射和其他系统寄存器。[Arm 的异常级切换示例](https://learn.arm.com/learning-paths/embedded-and-microcontrollers/bare-metal/exception-levels/) 可以对照这些寄存器看。

TF-A 的 [opteed_common.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/services/spd/opteed/opteed_common.c) 在初始化 OP-TEE 入口时设置 Secure 属性，并为 AArch64 选择 EL1 状态。这比一句“进入安全世界”更明确：这里准备的是安全内核入口，用户 TA 还没有开始执行。

世界切换也不是 CPU 自动把整套上下文全部打包。异常入口与软件保存、恢复要配合工作；TF-A 的 [EL3 上下文汇编](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/lib/el3_runtime/aarch64/context.S) 可以继续追到寄存器恢复及 `eret`。要理解某个状态为什么没有丢，应该找谁保存、谁恢复，而不是给 SMC 想象一个全能的副作用。

返回 Linux 时也是对应的交接：OP-TEE 在 S-EL1 发起 SMC，Monitor 恢复普通世界的上下文，再通过异常返回继续内核一侧的执行。注意，“回到 Linux”还可能只是为 RPC 暂时让出执行，不能据此判断 TA 的命令已经完成；这要继续看返回协议，第五篇再展开。[OP-TEE Core 的世界切换说明](https://optee.readthedocs.io/en/4.10.0/architecture/core.html) 可以和来时的路线放在一起读。

## 进入 OP-TEE 以后，还要再进一次用户态

用户 TA 和 pseudo TA 的区别在这里终于有了位置。前者由 OP-TEE 管理并运行在较低特权级；后者是编入 OP-TEE core 的服务接口，和安全内核处在同一特权级。两者都可能有 UUID 和会话接口，外面看起来相似，内部隔离却不一样。[OP-TEE 的 Trusted Applications 说明](https://optee.readthedocs.io/en/4.10.0/architecture/trusted_applications.html) 专门区分了这两种形式。

我在固定 OP-TEE OS 4.10.0 的 [thread_a64.S](https://github.com/OP-TEE/optee_os/blob/753afbbee1682f5d16fd30e87b31058a4fd4f4b8/core/arch/arm/kernel/thread_a64.S) 中核对了 `__thread_enter_user_mode`：它准备用户栈、`ELR_EL1` 与 `SPSR_EL1`，然后转向 `eret_to_el0`。这次是安全世界内部从 S-EL1 进入 S-EL0，并没有回到 Linux。用户 TA 通过系统调用请求安全内核服务时，使用的是 SVC 路径，也不能把它和切换世界的 SMC 混在一起。

所以一次 CA 请求里至少要分清两类边界：Linux 与固件、TEE 之间的交接，以及 OP-TEE 内核与用户 TA 之间的交接。把 TA 直接画在 EL3，就会同时丢掉这两层职责，也容易误以为 TA 写错一个指针等于直接写坏 Monitor。

## 这一篇核对到哪里了

本篇要交代的是这套部署为什么这样划分异常级，以及对应代码在哪里准备和恢复执行状态。证据分成三部分：Arm 架构资料说明指令与寄存器含义；固定源码说明 TF-A、OP-TEE 怎么使用它们；实际构建配置用来确认跑的是本文讨论的分支。

目前已核对 opteed 入口准备、EL3 返回汇编和 OP-TEE 用户态入口。以下是读者在锁定源码工作区中复查位置的命令，不是实验脚本生成的寄存器记录：

```sh
# 在锁定版本的 OP-TEE workspace 根目录执行
git -C trusted-firmware-a rev-parse HEAD
git -C optee_os rev-parse HEAD
rg -n 'opteed_smc_handler|cm_set_next_eret_context' \
  trusted-firmware-a/services/spd/opteed
rg -n '__thread_enter_user_mode|eret_to_el0' \
  optee_os/core/arch/arm/kernel/thread_a64.S
```

这次构建运行在 Ubuntu 22.04 的 GitHub Actions 宿主机上，[实验任务 35257180558](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558) 已通过。[导出的 manifest](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/repo-manifest.resolved.xml) 保存实际组件提交，[生成配置摘录](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/actual-config.txt) 中有 `CONFIG_ARM64=y`、`CONFIG_OPTEE=y` 和 `BR2_aarch64=y`。本次[运行脚本固定在 113865db](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/run-qemu.py)，便于连同构建参数一起检查。

普通世界的 [UART 记录](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-normal.txt) 给出了一个和这篇直接相关的观测：

```text
[    0.131470] CPU: All CPU(s) started at EL1
```

这行是 Linux 对启动异常级的报告，支持本次 Linux 从 EL1 开始的判断。我没有在 CA、Monitor、OP-TEE 和用户 TA 的每个入口逐一采样 `CurrentEL`、PC 或返回寄存器；图中其余位置由构建配置、架构资料和固定源码共同说明。以后如果补汇编单步实验，才需要附上各入口的寄存器记录，不能让一行启动日志替整张图做完所有验证。

读到这里，我暂时不需要背完所有系统寄存器。下次再遇到一条箭头，先写清楚起点和终点的安全状态、异常级，再去找触发异常和恢复上下文的代码，至少不会在第一步就走错方向。下一篇把视角拉回 Linux，从 `/dev/tee0` 看这次请求怎样进入内核。

本篇示意图与叙述为自行整理，没有复制官方图。引用的 TF-A 文件按上游标注采用 BSD-3-Clause，OP-TEE 汇编文件采用 BSD-2-Clause；本文未整段转载实现，复用源码时应保留原文件的版权与许可证声明。

系列目录：[01 CA 到 TA](/post/tee-01-ca-to-ta.html) · **02 异常级** · [03 Linux 驱动](/post/tee-03-linux-tee-driver.html) · [04 共享内存](/post/tee-04-shared-memory.html) · [05 RPC](/post/tee-05-rpc-and-supplicant.html) · [06 启动](/post/tee-06-before-the-first-call.html)

上一篇：[一次 CA 请求，到底怎么走到 TA？](/post/tee-01-ca-to-ta.html)　下一篇：[从 /dev/tee0 开始，追一次请求进入内核](/post/tee-03-linux-tee-driver.html)
