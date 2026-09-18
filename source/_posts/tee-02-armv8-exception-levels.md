---
title: 看 TEE 代码之前，我先把 ARMv8 的异常级理清了
date: "2026-09-06T08:00:00+08:00"
updated: "2026-09-18T08:54:38+08:00"
tags: [ARMv8, TrustZone, TEE, OP-TEE]
categories: [系统安全]
description: 把异常级、安全状态和执行状态拆开，再沿着一次 OP-TEE 请求看 SMC、ERET 和上下文切换各自负责什么。
series: 顺着一次 TEE 调用
series_order: 2
permalink: /post/tee-02-armv8-exception-levels.html
---

追 CA 到 TA 的调用链时，有个地方需要停下来：Linux 内核在 NS-EL1，用户 TA 在 S-EL0，为什么 EL 数字更大的 Linux 不能直接访问 TA 的内存？只用“权限高低”解释这条路径，会漏掉安全状态。

还有一个疑问在 TF-A 里：Monitor 为什么能靠 `ERET` 进入 OP-TEE？名字明明叫“异常返回”，目标却是另一边的安全内核。这两个问题都需要把代码所在的异常级和安全状态写清楚。

## 异常级和安全状态分别管什么

Exception Level 描述异常级，影响指令、系统寄存器和特权操作；Security state 描述安全状态，参与访问隔离；Execution state 则区分 AArch64 与 AArch32。读代码时，这三项都要看。本文采用传统 TrustZone 的两个安全状态和 AArch64 部署，暂不讨论 Realm 及虚拟化后的异常路由。概念可以对照 [Arm 的 AArch64 Exception Model，第 2、3 章](https://documentation-service.arm.com/static/63a065c41d698c4dc521cb1c)。

下面这张图对应本系列的配置。S 和 NS 分别表示 Secure、Non-secure，EL3 负责安全状态之间的管理，图中两侧共用这一层 Monitor。

![传统 SMC 部署中的异常级与安全状态](/post/tee-02-armv8-exception-levels/architecture.svg)

| 本系列中的代码 | 所在位置 | 它直接负责的事情 |
| --- | --- | --- |
| CA、libteec、tee-supplicant | NS-EL0 | 用户态业务、客户端封装和普通世界服务 |
| Linux 内核、TEE 驱动 | NS-EL1 | 内核接口、参数转换和与固件通信 |
| TF-A BL31、opteed | EL3 | 固件服务分发及安全上下文交接 |
| OP-TEE core、pseudo TA | S-EL1 | 安全内核及其中的特权服务 |
| 用户 TA | S-EL0 | 经安全内核管理的应用代码 |

[build-config.txt](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/build-config.txt) 记录了 `SPMC_AT_EL=n`、`SPD=opteed`。普通世界和安全世界的用户、内核四侧均为 64 位：`COMPILE_NS_USER`、`COMPILE_NS_KERNEL`、`COMPILE_S_USER`、`COMPILE_S_KERNEL` 都是 `64`，对应固定版本 [qemu_v8.mk](https://github.com/OP-TEE/build/blob/53bfd321ee7fd47e450fb88c04b08ea27819f9bc/qemu_v8.mk) 的传统 SMC 分支。表里的位置由这套部署决定，Linux 在其他配置中也可能运行于不同异常级。

实际启动命令选了 QEMU `virt` 机器、`virtualization=false` 和 `-cpu max,sme=on,pauth-impdef=on`。这里的 `max` 按模拟器支持情况启用处理器特性；[固定 QEMU 源码](https://github.com/qemu/qemu/blob/7c949c53e936aa3a658d84ab53bae5cadaa5d59c/target/arm/tcg/cpu64.c) 也特意让它区别于真实 CPU 型号。实验中的特性组合不能直接当成某颗 Armv8.0 芯片的规格。

这条调用路径没有经过 EL2，异常也不要求按 EL0、EL1、EL2、EL3 逐级发生。某些 Armv8 扩展支持 Secure EL2，FF-A/SPM 还有其他部署组合；换一套配置时，需要重新核对组件的位置和异常路由。

## 在 Linux 里已经是 root，为什么还过不去

root 是 Linux 管理的用户身份。root 进程运行用户代码时仍处于用户态，通过系统调用进入内核后，也仍在 Non-secure 状态。Linux 内部的提权不会把一次 Non-secure 内存访问改成 Secure 访问。

安全侧也有自己的权限划分。用户 TA 在 S-EL0，受 OP-TEE 建立的映射与权限约束，不能任意修改安全内核的页表和数据。所以看一次访问是否合法，既要看当前代码的特权，也要看访问所属的安全状态。

CA 传入的指针还涉及地址空间。这个地址属于 CA 进程；驱动和 OP-TEE 要按协议处理缓冲区，TA 得到的是安全侧建立的映射。两边地址的数值即使相同，也不能据此认定它们指向同一块内存。第四篇会继续看这部分参数转换。

## `opteed_smc_handler()` 接到的是什么

CA 调用 `TEEC_InvokeCommand()`，经过 libteec 和系统调用进入 Linux 内核，OP-TEE 驱动才会发起与固件的通信。在本系列配置下，SMC 引发到 EL3 的异常，由 TF-A 分发。此时还没有执行到 TA 的业务函数。

在固定 TF-A v2.14.0 的 [opteed_main.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/services/spd/opteed/opteed_main.c) 中，可以找到 `opteed_smc_handler()`。它为普通世界发来的合法 OP-TEE 调用选择安全入口，准备上下文，再交给 EL3 的退出路径。代码里区分了 fast 和 yielding 入口，hello_world 的 command 则要到后面的 TEE 消息处理和 TA 分发中才能找到。

追参数时有几个编号容易看串。SMC Function ID 标识固件服务，OP-TEE 消息说明要开会话还是发命令，UUID 标识目标 TA，TA 的 command ID 选择应用操作。SMC 本身只提供异常机制。这些字段要在各自的接口定义中查，不能拿一个编号去解释另一层的行为。

这里的“SMC 到 EL3”以没有相关虚拟化拦截为条件。架构允许高一级软件配置陷入控制，虚拟机里的调用需要另外检查路由。EL0 程序也不能直接用 SMC 调用 TEE，仍要经过用户接口和驱动。

## `ERET` 使用谁的上下文

SMC 引发异常，`ERET` 执行异常返回。我读到这里才弄清楚，“返回”要去哪里取决于软件准备的上下文，并不固定为刚才那条 SMC 的下一条指令。Monitor 可以据此进入 OP-TEE，也可以恢复先前暂停的普通世界执行。

在 EL3 的退出路径里，`ELR_EL3` 给出返回地址，`SPSR_EL3` 提供需要恢复的处理器状态；在本文的两种安全状态模型下，`SCR_EL3.NS` 参与选择低异常级的安全状态。目标环境还需要正确的栈、映射和其他系统寄存器，单独设置返回地址并不够。[Arm 的异常级切换示例](https://learn.arm.com/learning-paths/embedded-and-microcontrollers/bare-metal/exception-levels/) 可以对照着看。

TF-A 的 [opteed_common.c](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/services/spd/opteed/opteed_common.c) 在初始化 OP-TEE 入口时设置 Secure 属性，并为 AArch64 选择 EL1 状态，对应图中的安全内核 S-EL1。用户 TA 要由 OP-TEE 继续调度。

切换时，上下文的保存和恢复需要软件参与。TF-A 的 [EL3 上下文汇编](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/lib/el3_runtime/aarch64/context.S) 里能继续追到寄存器恢复及 `eret`。如果关心某个寄存器在切换后为何仍保留原值，就要查它对应的保存位置和恢复代码，不能把所有状态都当成 SMC 自动处理了。

返回 Linux 时，OP-TEE 在 S-EL1 发起 SMC，Monitor 恢复普通世界上下文，通过异常返回继续内核一侧的执行。返回原因可能是命令完成，也可能是请求 RPC 服务，驱动需要按返回协议区分。第五篇会展开 RPC；这里可以参考 [OP-TEE Core 的世界切换说明](https://optee.readthedocs.io/en/4.10.0/architecture/core.html)。

## OP-TEE 怎样进入用户 TA

用户 TA 由 OP-TEE 管理，运行在 S-EL0；pseudo TA 编入 OP-TEE core，与安全内核同处 S-EL1。它们都可能提供 UUID 和会话接口，但接口相似并不表示隔离方式相同。[OP-TEE 的 Trusted Applications 说明](https://optee.readthedocs.io/en/4.10.0/architecture/trusted_applications.html) 对这两种形式有具体说明。

我在固定 OP-TEE OS 4.10.0 的 [thread_a64.S](https://github.com/OP-TEE/optee_os/blob/753afbbee1682f5d16fd30e87b31058a4fd4f4b8/core/arch/arm/kernel/thread_a64.S) 中查到 `__thread_enter_user_mode`：它准备用户栈、`ELR_EL1` 与 `SPSR_EL1`，然后转向 `eret_to_el0`。这次异常返回发生在安全世界内部，从 S-EL1 进入 S-EL0。用户 TA 请求安全内核服务时走 SVC 路径，整个过程可以留在安全世界中。

因此，从 Linux 到 OP-TEE 的世界切换之后，还要经过安全内核到用户 TA 的权限切换。用户 TA 并不运行在 EL3，它访问错误地址时受到的约束也与 Monitor 不同。

## 对照配置和启动日志

上面涉及的 opteed 入口、EL3 返回汇编和 OP-TEE 用户态入口，可以在锁定版本的工作区中用这些命令定位：

```sh
# 在锁定版本的 OP-TEE workspace 根目录执行
git -C trusted-firmware-a rev-parse HEAD
git -C optee_os rev-parse HEAD
rg -n 'opteed_smc_handler|cm_set_next_eret_context' \
  trusted-firmware-a/services/spd/opteed
rg -n '__thread_enter_user_mode|eret_to_el0' \
  optee_os/core/arch/arm/kernel/thread_a64.S
```

[9 月 18 日的实验记录 35257180558](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558) 来自 Ubuntu 22.04 的 GitHub Actions 宿主机。[导出的 manifest](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/repo-manifest.resolved.xml) 保存实际组件提交，[生成配置摘录](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/actual-config.txt) 中有 `CONFIG_ARM64=y`、`CONFIG_OPTEE=y` 和 `BR2_aarch64=y`。[运行脚本固定在 113865db](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/run-qemu.py)，可以连同构建参数一起复查。

普通世界的 [UART 记录](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-normal.txt) 中，Linux 报告了启动异常级：

```text
[    0.131470] CPU: All CPU(s) started at EL1
```

这行记录支持本次 Linux 从 EL1 开始的判断。CA、Monitor、OP-TEE 和用户 TA 各入口的 `CurrentEL`、PC 及返回寄存器没有逐一采样；图中其他位置依据构建配置、架构资料和固定源码确定。要直接观察每一次切换，还需要另外做单步或入口采样。

下一篇回到 Linux，从 `/dev/tee0` 和 ioctl 继续追驱动收到请求后的处理。

示意图为自行整理。引用的 TF-A 文件采用 BSD-3-Clause，OP-TEE 汇编文件采用 BSD-2-Clause；复用源码时应保留原文件的版权与许可证声明。

系列目录：[01 CA 到 TA](/post/tee-01-ca-to-ta.html) · **02 异常级** · [03 Linux 驱动](/post/tee-03-linux-tee-driver.html) · [04 共享内存](/post/tee-04-shared-memory.html) · [05 RPC](/post/tee-05-rpc-and-supplicant.html) · [06 启动](/post/tee-06-before-the-first-call.html)

上一篇：[一次 CA 请求，到底怎么走到 TA？](/post/tee-01-ca-to-ta.html)　下一篇：[从 /dev/tee0 开始，追一次请求进入内核](/post/tee-03-linux-tee-driver.html)
