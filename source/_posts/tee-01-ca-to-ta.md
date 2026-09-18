---
title: 一次 CA 请求，到底怎么走到 TA？
date: "2026-09-03T08:00:00+08:00"
updated: "2026-09-18T08:54:38+08:00"
tags: [TEE, OP-TEE, Linux, ARMv8]
categories: [系统安全]
description: 从官方 hello_world 出发，把 CA、libteec、Linux TEE 驱动、Secure Monitor 和用户 TA 接成一条能追踪的调用链。
series: 顺着一次 TEE 调用
series_order: 1
permalink: /post/tee-01-ca-to-ta.html
---

OP-TEE 官方的 `hello_world` 很短：CA 传入 42，TA 加一，CA 收到 43。单看应用代码，只能看到几个 `TEEC_` 函数，安全世界的切换藏在了调用后面。

我从这个例子往下读，先查参数怎么交给 Linux 驱动，再查驱动怎样进入 OP-TEE。加一本身没有多少业务逻辑，正好用来对照各层接口和两侧日志。

## 这次调用经过哪些组件

实验使用 OP-TEE 4.10.0 的 QEMU Armv8-A 配置，采用传统 SMC 通信路径。下面的调用链以这组软件和配置为准，其他 TrustZone 平台可能有不同的部署方式。

![CA 到用户 TA 的调用链与返回路径](/post/tee-01-ca-to-ta/architecture.svg)

CA，也就是 Client Application，是 Linux 里的普通用户进程，对应示例中的 host 程序。TA 是 Trusted Application，由 OP-TEE 管理。hello_world 使用的是**用户 TA**，有自己的用户态执行环境；另一类 pseudo TA 编进 OP-TEE 内核，以内核权限运行。[OP-TEE TA 类型说明](https://optee.readthedocs.io/en/4.10.0/architecture/trusted_applications.html)

CA 调用的 `TEEC_` 接口由 libteec 提供。libteec 整理请求，再通过 Linux TEE 的设备接口进入内核。TEE core 处理通用用户接口，OP-TEE 驱动处理 OP-TEE 的消息与底层通信。到这里，都还在普通世界。

驱动通过选定的 SMC conduit 发起调用，由 EL3 的 Secure Monitor 及 OP-TEE dispatcher 协调切换到 OP-TEE。Monitor 处理跨世界的控制交接。OP-TEE 收到消息后处理会话、参数和目标应用，最后进入 TA 的命令入口，加一的代码才会执行。CA 无法直接跳到这个入口，中间各层通过约定的接口和消息格式传递请求。[Linux TEE 接口](https://docs.kernel.org/userspace-api/tee.html)、[TF-A OP-TEE dispatcher](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/services/spd/opteed/opteed_main.c)

## Context、Session 和 Command

在 [hello_world 的 CA 源码](https://github.com/linaro-swg/optee_examples/blob/934c7edb74a26e90f68024cf441073528444177f/hello_world/host/main.c)里，几个主要接口按下面的顺序调用：

```text
InitializeContext → OpenSession → InvokeCommand
                                      ↓
FinalizeContext  ← CloseSession ← 返回结果
```

Context 表示客户端与一个 TEE 实现之间的连接上下文。当前 libteec 会尝试打开 `/dev/teeN`，查询接口版本与能力，选择符合要求的设备，再保留文件描述符等状态。初始化到这里，还没有选择或运行某个 TA，`/dev/tee0` 只是设备入口。[libteec 固定版本实现](https://github.com/OP-TEE/optee_client/blob/9f5e90918093c1d1cd264d8149081b64ab7ba672/libteec/src/tee_client_api.c)

Session 是面向目标 TA 的一次会话。打开会话时传入 UUID，标识要找哪个 TA；成功后得到的 session ID 用于后续调用。UUID 只负责标识，业务授权还需要另外处理。示例采用 `TEEC_LOGIN_PUBLIC`，演示公开登录方式下的接口调用，没有实现“一人一权限”的业务模型。

Command 是 TA 自己定义的操作编号。`TA_HELLO_WORLD_CMD_INC_VALUE` 只在这个示例的接口中表示加一，并非系统通用的调用号。同一个 Session 可以执行多个 Command，也可以多次执行同一 Command。是否允许并发、是否保留状态，要继续看 TA 的属性及实现。

## value 参数怎么传进去

官方 CA 准备了一个 value 参数，方向为 INOUT：输入侧给出 42，输出侧在同一个参数位置取回结果。其余三个参数槽标记为 NONE。Client API 提供四个参数槽，槽中可以放 value，也可以放描述一段内存的 memref，并不限制为四个整数。第四篇会继续看 memref。

TA 收到命令时，先检查参数类型组合，再读取参数、执行加一。`cmd_id` 与 `param_types` 都要满足接口约定：即使命令号正确，参数类型不对也必须拒绝，不能直接读取对应字段。[hello_world 的 TA 实现](https://github.com/linaro-swg/optee_examples/blob/934c7edb74a26e90f68024cf441073528444177f/hello_world/ta/hello_world_ta.c)

读到这里需要继续追参数转换。CA 里的 `TEEC_Operation` 不会原封不动传到 TA：libteec 先将参数转换成 Linux ioctl 使用的数据，驱动再转换成 OP-TEE 消息参数；进入用户 TA 前，OP-TEE 还要完成检查和映射。两边的地址空间不同，各层使用的参数表示也不同。

返回时，TA 给出结果，OP-TEE 写回消息中的返回值和输出参数，驱动交回 ioctl 参数，libteec 再把输出整理回 CA 的 operation。CA 最后读取的仍然是自己的结构体。

## OpenSession 也会进入安全侧

TA 未必已经装入安全内存。对于存放在 REE 文件系统的用户 TA，首次打开会话可能触发加载。OP-TEE 请求普通世界提供 TA 文件，经 tee-supplicant 取回后，由安全侧验证和装载。因此，`OpenSession` 就可能包含两侧的往返，进入安全世界的时机要早于 `InvokeCommand`。[REE TA 加载实现](https://github.com/OP-TEE/optee_os/blob/753afbbee1682f5d16fd30e87b31058a4fd4f4b8/core/kernel/ree_fs_ta.c)

用户 TA 的创建、打开会话、执行命令、关闭会话和销毁，也有不同入口。创建实例与打开 Session 不是一回事，不能简单地按“每次 OpenSession 都创建一个新 TA 进程”理解；实例复用和存活策略受 TA flags 影响。官方 hello_world 会在会话入口打印问候，在命令入口处理数字。仅看到问候语，最多说明执行到相应入口，不能替代加一结果的验证。

SMC 返回 Linux 也可能只是请求普通世界提供服务，之后还要恢复安全侧执行。判断命令是否结束，需要看返回协议。这部分 RPC 流程放在第五篇。

## QEMU 中的运行记录

下面是 2026 年 9 月 18 日的实验记录，来自 [GitHub Actions 任务 35257180558](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558)。宿主机是 Ubuntu 22.04，QEMU 运行 AArch64 的来宾系统。依赖、固定源码与复现方法放在仓库的[公开实验包](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/README.md)。

实验包沿用 [OP-TEE 官方 QEMU Armv8-A 方案](https://optee.readthedocs.io/en/4.10.0/building/devices/qemu.html#qemu-v8)，锁定 manifest、校验各项目提交，并保存实际的 [`repo manifest -r`](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/repo-manifest.resolved.xml)，方便之后按同一版本复查。下面是依赖准备完成后的脚本入口，`OPTEE_LAB_ROOT` 指向 `/home/runner/optee-series`：

```sh
# 从博客仓库根目录执行；依赖与 OPTEE_LAB_ROOT 已由工作流准备
bash labs/optee-series/bootstrap-linux.sh "$OPTEE_LAB_ROOT"
bash labs/optee-series/series-make.sh "$OPTEE_LAB_ROOT" aarch64-toolchain
JOBS=4 bash labs/optee-series/build-linux.sh "$OPTEE_LAB_ROOT"
python3 labs/optee-series/run-qemu.py "$OPTEE_LAB_ROOT"
```

工具链只调用 `aarch64-toolchain` 目标；通用目标还会安装其他工具链。`series-make.sh` 固定四侧为 64 位、`SPMC_AT_EL=n`、`TF_A_TRUSTED_BOARD_BOOT=n`，关闭 Rust 示例与 fTPM，并加入 strace 和安全侧日志配置。复现时需要保留这些选项，上游默认配置与本次实验有差别。

本次执行的 [`run-qemu.py`](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/run-qemu.py) 将普通世界接到交互串口，将安全世界写入独立日志。它在来宾里通过 strace 运行官方示例，并保存退出状态。手动查看应用本身时，核心命令仍然只有：

```sh
optee_example_hello_world
printf 'exit=%s\n' "$?"
```

实际的 [CA 输出](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/hello-world.txt) 是：

```text
Invoking TA to increment 42
TA incremented value to 43
```

程序退出码为 0。[安全侧串口](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-secure.txt) 对应部分按原顺序摘录如下，省略号表示删去的内核日志：

```text
D/TA:  TA_CreateEntryPoint:18 has been called
D/TA:  __GP11_TA_OpenSessionEntryPoint:47 has been called
I/TA: Hello World!
D/TA:  inc_value:78 has been called
I/TA: Got value: 42 from NW
I/TA: Increase value to: 43
...
I/TA: Goodbye!
D/TA:  TA_DestroyEntryPoint:29 has been called
```

CA 与 TA 的输入、输出一致。[CA 的 strace](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/hello-world.strace.txt)还记录了中间的接口数据：打开会话的 UUID 是 `8aaaf200-2450-11e4-abe2-0002a5d5c51b`，得到 `session=0x2`；随后 `TEE_IOC_INVOKE` 中的 `a` 从 `0x2a` 变成 `0x2b`，返回值为 0，来源为 `TEEC_ORIGIN_TRUSTED_APP`。安全侧也记录了这个 UUID 的 ELF 装载和会话 2 的关闭。这里的会话号只属于本次运行，TA 本身由 UUID 标识。

这次没有逐层设置断点。应用、ioctl 和 TA 日志是运行观察；Monitor 怎样交接、消息怎样转换，则依据前面的固定源码。第三篇会展开这份 strace。

排查失败时，需要保留返回码和 error origin，并确认失败发生在哪个接口。Context 初始化失败要检查可用设备，OpenSession 失败可能与目标 TA 的查找和加载有关，InvokeCommand 返回参数错误则要对照 TA 的命令实现。

还有一个问题没有展开：图里的用户进程、Linux 内核、Monitor 和 TA 分别处在哪个异常级，安全状态又在哪里切换？第二篇继续看这部分。

## 版本与出处

本系列采用 [manifest 4.10.0 对应提交](https://github.com/OP-TEE/manifest/tree/6d5849d5c1e4054980bf430ce1e96ebd0f532590)，本文源码链接固定到该版本选定的组件提交，OP-TEE 文档也使用 4.10.0 版本。公开示例为 Linaro 的 BSD-2-Clause 代码；上述调用顺序是阅读说明，复现实验使用上游原文件并保留其版权和许可证。

系列目录：[01 调用链](/post/tee-01-ca-to-ta.html) · [02 ARMv8 异常级](/post/tee-02-armv8-exception-levels.html) · [03 Linux 驱动](/post/tee-03-linux-tee-driver.html) · [04 共享内存](/post/tee-04-shared-memory.html) · [05 RPC](/post/tee-05-rpc-and-supplicant.html) · [06 启动过程](/post/tee-06-before-the-first-call.html)

下一篇：[看 TEE 代码之前，我先把 ARMv8 的异常级理清了](/post/tee-02-armv8-exception-levels.html)。
