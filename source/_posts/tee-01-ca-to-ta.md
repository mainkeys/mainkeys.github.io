---
title: 一次 CA 请求，到底怎么走到 TA？
date: "2026-09-18T03:20:04+08:00"
tags: [TEE, OP-TEE, Linux, ARMv8]
categories: [系统安全]
description: 从官方 hello_world 出发，把 CA、libteec、Linux TEE 驱动、Secure Monitor 和用户 TA 接成一条能追踪的调用链。
series: 顺着一次 TEE 调用
series_order: 1
permalink: /post/tee-01-ca-to-ta.html
---

我现在想补的，不是再背一遍 CA、TA、TEE 分别是什么。

这些缩写单独看都不复杂。真正让我想停下来整理的，是把它们放到一起之后：应用调用了一个函数，怎么就跑进安全世界了？中间到底谁负责传参数，谁负责切换状态，最后又是谁执行真正的业务？

所以这一轮先不做加密、不碰密钥，也不把架构图画成一座立交桥。就用 OP-TEE 官方 `hello_world`：普通应用传进去一个数，让 TA 加一，再把结果拿回来。业务简单一点，才容易看清楚路是怎么走的。

## 加一这件事，居然需要这么多人

这篇选择 OP-TEE 4.10.0 的 QEMU Armv8-A 配置，采用传统 SMC 通信路径。它对应一组具体的软件和配置，不代表所有 TrustZone 产品都长这样。

![CA 到用户 TA 的调用链与返回路径](/post/tee-01-ca-to-ta/architecture.svg)

CA，也就是 Client Application，首先是 Linux 里的普通用户进程。官方示例的 host 程序属于这一侧；TA，也就是 Trusted Application，属于 OP-TEE 管理的一侧。这里说的 TA 是**用户 TA**，有自己的用户态执行环境，不要把它与编进 OP-TEE 内核、以内核权限运行的 pseudo TA 混为一谈。[OP-TEE TA 类型说明](https://optee.readthedocs.io/en/4.10.0/architecture/trusted_applications.html)

CA 调用的 `TEEC_` 接口由 libteec 提供。libteec 整理请求，再通过 Linux TEE 的设备接口进入内核。TEE core 处理通用用户接口，OP-TEE 驱动处理 OP-TEE 的消息与底层通信。到这里，都还在普通世界。

继续向下，驱动通过选定的 SMC conduit 发起调用，由 EL3 的 Secure Monitor 及 OP-TEE dispatcher 协调切换到 OP-TEE。Monitor 负责跨世界的控制交接，不负责替 TA 加一。OP-TEE 收到消息后处理会话、参数和目标应用，最后进入 TA 的命令入口。[Linux TEE 接口](https://docs.kernel.org/userspace-api/tee.html)、[TF-A OP-TEE dispatcher](https://github.com/TrustedFirmware-A/trusted-firmware-a/blob/1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc/services/spd/opteed/opteed_main.c)

把层次分清之后，我反而觉得没那么玄了。应用不能直接跳到另一个世界的函数地址，中间就需要明确的接口、消息格式和执行权限。

## Context、Session、Command，到底谁管谁

看 [hello_world 的 CA 源码](https://github.com/linaro-swg/optee_examples/blob/934c7edb74a26e90f68024cf441073528444177f/hello_world/host/main.c)，主线可以整理成下面这样。这里只是调用顺序，不是可以独立编译的程序：

```text
InitializeContext → OpenSession → InvokeCommand
                                      ↓
FinalizeContext  ← CloseSession ← 返回结果
```

Context 表示客户端与一个 TEE 实现之间的连接上下文。初始化 Context 不等于运行了某个 TA。当前 libteec 会尝试打开 `/dev/teeN`，查询接口版本与能力，选择符合要求的设备，再保留文件描述符等状态。因此常见的 `/dev/tee0` 是设备入口，不是一个叫“tee0”的 TA。[libteec 固定版本实现](https://github.com/OP-TEE/optee_client/blob/9f5e90918093c1d1cd264d8149081b64ab7ba672/libteec/src/tee_client_api.c)

Session 是面向目标 TA 的一次会话。打开会话时传入 UUID，由它标识要找哪个 TA。成功后得到的 session ID 则用于后续调用，两者用途不同。UUID 不是密码，知道 UUID 也不等于完成了业务授权；示例采用 `TEEC_LOGIN_PUBLIC`，它演示的是公开登录方式下的接口调用，没有实现“一人一权限”的业务模型。

Command 是 TA 自己定义的操作编号。`TA_HELLO_WORLD_CMD_INC_VALUE` 表示示例中的加一命令，不是整个系统通用的“加一系统调用”。同一个 Session 可以执行多个 Command，也可以多次执行同一 Command。是不是允许并发、是否保留状态，还要看 TA 的属性及实现。

我更愿意这样区分：Context 解决怎么接入 TEE，Session 解决这次和哪个 TA 交流，Command 解决请这个 TA 做哪件事。它们不是把一个连接起了三个名字。

## 从 42 到 43，参数也有自己的约定

官方 CA 准备的是一个 value 参数，方向为 INOUT：输入侧给出 42，输出侧在同一个参数位置取回结果。其余三个参数槽标记为 NONE。这里的“四个”来自 Client API 的参数模型，不能顺手推广成“TEE 只能传四个整数”。传较大的数据还可以用 memref，第四篇会单独追这部分。

TA 收到命令时，先检查参数类型组合，再读取参数、执行加一。也就是说，`cmd_id` 与 `param_types` 要一起满足接口约定。只认命令号，不管参数是什么，就相当于看到包裹单号正确便直接拆包使用，里面装的是什么完全不问。[hello_world 的 TA 实现](https://github.com/linaro-swg/optee_examples/blob/934c7edb74a26e90f68024cf441073528444177f/hello_world/ta/hello_world_ta.c)

需要注意，CA 里的 `TEEC_Operation` 不会原封不动变成 TA 里的 C 结构体。libteec 将参数转换成 Linux ioctl 使用的数据，驱动再转换成 OP-TEE 消息参数；进入用户 TA 前，OP-TEE 还要完成相应检查和映射。这些转换让用户进程里的表示方式与安全侧的表示方式接上，而不是假设两边可以共用一个进程地址空间。

返回同样要经过这几层：TA 给出结果，OP-TEE 写回消息中的返回值和输出参数，驱动交回 ioctl 参数，libteec 再把输出整理回 CA 的 operation。上面的箭头看着像一次普通函数调用，实际已经跨过了好几道边界。

## 打开会话时，也可能已经很忙了

容易漏掉的一点是：TA 不是一定早就在安全内存里等着。

对存放在 REE 文件系统的用户 TA，首次打开会话可能触发加载。OP-TEE 请求普通世界提供 TA 文件，经 tee-supplicant 取回后，还需要安全侧验证和装载。于是 `OpenSession` 这一步就可能包含往返，而不是只有 `InvokeCommand` 才进入安全世界。[REE TA 加载实现](https://github.com/OP-TEE/optee_os/blob/753afbbee1682f5d16fd30e87b31058a4fd4f4b8/core/kernel/ree_fs_ta.c)

用户 TA 的创建、打开会话、执行命令、关闭会话和销毁，也有不同入口。创建实例与打开 Session 不是一回事，不能简单地按“每次 OpenSession 都创建一个新 TA 进程”理解；实例复用和存活策略受 TA flags 影响。官方 hello_world 会在会话入口打印问候，在命令入口处理数字。仅看到问候语，最多说明执行到相应入口，不能替代加一结果的验证。

同样，SMC 返回 Linux 也不一定表示整个命令结束。返回可能是在请求普通世界提供服务，之后还要恢复安全侧执行。第五篇会把这个往返拆开，现在先在图旁边记下这个例外，免得以后拿一张直线图解释所有日志。

## 把 42 到 43 真正跑一遍

这次实验运行在独立的 [GitHub Actions 任务 35257180558](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558) 中，宿主机是 Ubuntu 22.04，QEMU 运行 AArch64 的来宾系统。依赖、固定源码与复现方法放在本仓库的[公开实验包](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/README.md)。使用 CI 的一个好处是，文章里的结果能对应到一次具体运行，而不是只剩下我电脑上的几行截图。

实验包沿用 [OP-TEE 官方 QEMU Armv8-A 方案](https://optee.readthedocs.io/en/4.10.0/building/devices/qemu.html#qemu-v8)，先锁定 manifest，再校验各项目提交，保存实际的 [`repo manifest -r`](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/repo-manifest.resolved.xml)。只记“用了最新代码”，过几个月就很难对上了。下面是依赖准备完成后的脚本入口，`OPTEE_LAB_ROOT` 指向 `/home/runner/optee-series`：

```sh
# 从博客仓库根目录执行；依赖与 OPTEE_LAB_ROOT 已由工作流准备
bash labs/optee-series/bootstrap-linux.sh "$OPTEE_LAB_ROOT"
bash labs/optee-series/series-make.sh "$OPTEE_LAB_ROOT" aarch64-toolchain
JOBS=4 bash labs/optee-series/build-linux.sh "$OPTEE_LAB_ROOT"
python3 labs/optee-series/run-qemu.py "$OPTEE_LAB_ROOT"
```

这次只调用 `aarch64-toolchain`，不使用还会安装其他工具链的通用目标。`series-make.sh` 固定四侧为 64 位、`SPMC_AT_EL=n`、`TF_A_TRUSTED_BOARD_BOOT=n`，关闭本次不需要的 Rust 示例与 fTPM，并加入 strace 和安全侧日志配置。它们是本系列选定的实验条件，不是把所有上游默认值原样照搬。

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

这两段合起来，才把“发出 42、执行加一、收到 43”接上了。中间还有一份 [CA 的 strace](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/hello-world.strace.txt)：打开会话的 UUID 是 `8aaaf200-2450-11e4-abe2-0002a5d5c51b`，得到 `session=0x2`；随后 `TEE_IOC_INVOKE` 中的 `a` 从 `0x2a` 变成 `0x2b`，返回值为 0，来源为 `TEEC_ORIGIN_TRUSTED_APP`。安全侧也记录了这个 UUID 的 ELF 装载和会话 2 的关闭。这里的会话号只属于本次运行，不是 TA 的固定编号。

我没有在每一层加断点，因此不会把图里的每根箭头都说成逐条单步得到。应用、ioctl 和 TA 日志提供运行观察；Monitor 怎样交接、消息怎样转换，则由前面的固定源码解释。第三篇再把这份 strace 拆开看。

如果程序失败，我会先保留返回码和 error origin，而不是只截最后一句“失败”。Context 失败、会话失败、命令失败，排查方向完全不同。驱动没有可用设备、TA 找不到、TA 拒绝参数，也不能都塞进一个“TEE 有问题”的筐里。

这篇先把后面查代码需要的几个位置放好。接下来我想把图里的 EL0、EL1、EL3 讲明白：既然经过了这么多层，它们到底是在换进程、换权限，还是换安全状态？

## 版本与出处

本系列采用 [manifest 4.10.0 对应提交](https://github.com/OP-TEE/manifest/tree/6d5849d5c1e4054980bf430ce1e96ebd0f532590)，本文源码链接固定到该版本选定的组件提交，OP-TEE 文档也使用 4.10.0 版本。公开示例为 Linaro 的 BSD-2-Clause 代码；上述调用顺序是阅读说明，复现实验使用上游原文件并保留其版权和许可证。

系列目录：[01 调用链](/post/tee-01-ca-to-ta.html) · [02 ARMv8 异常级](/post/tee-02-armv8-exception-levels.html) · [03 Linux 驱动](/post/tee-03-linux-tee-driver.html) · [04 共享内存](/post/tee-04-shared-memory.html) · [05 RPC](/post/tee-05-rpc-and-supplicant.html) · [06 启动过程](/post/tee-06-before-the-first-call.html)

下一篇：[看 TEE 代码之前，我先把 ARMv8 的异常级理清了](/post/tee-02-armv8-exception-levels.html)。
