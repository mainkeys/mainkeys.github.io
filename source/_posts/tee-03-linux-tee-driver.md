---
title: 从 /dev/tee0 开始，追一次请求进入内核
date: "2026-09-07T08:00:00+08:00"
updated: "2026-09-19T08:30:00+08:00"
tags: [Linux, Kernel, Driver, TEE, OP-TEE]
categories: [系统安全]
description: 沿着 libteec 的 ioctl 请求，分清 TEE core 与 OP-TEE 驱动的职责，也把 probe 和运行期调用放回各自的位置。
series: 顺着一次 TEE 调用
series_order: 3
permalink: /post/tee-03-linux-tee-driver.html
---

`TEEC_InvokeCommand()` 最终会通过 ioctl 进入 Linux。继续查内核代码，就会碰到 `probe`、`file_operations` 和几张操作表，调用关系开始绕起来了。

我读这一段时先把初始化和运行期分开。`probe` 负责准备设备和回调；hello_world 发出请求时，沿着已经建立的回调关系进入驱动。下面先查这些回调在哪里注册，再用实际 strace 对照请求顺序。

## 设备节点和目标 TA

普通应用通过 `/dev/teeN` 使用 Linux TEE 用户接口，tee-supplicant 则通过 `/dev/teeprivN` 接收需要普通世界协助处理的请求。`N` 是注册得到的编号，其他系统上不一定为 0。CA 打开的是 TEE 设备节点，TA 文件由另外的加载流程处理。[Linux TEE 用户接口说明](https://docs.kernel.org/userspace-api/tee.html)

当前 libteec 初始化 Context 时，会尝试设备节点，通过 `TEE_IOC_VERSION` 查询实现及能力，再判断是否符合要求。选定设备后，后续请求使用打开节点得到的文件描述符；目标 TA 的 UUID 到打开会话时才传入。[libteec 的设备发现逻辑](https://github.com/OP-TEE/optee_client/blob/9f5e90918093c1d1cd264d8149081b64ab7ba672/libteec/src/tee_client_api.c)

这次来宾中出现的是 `/dev/tee0` 和 `/dev/teepriv0`，CA 的跟踪记录打开了前者。节点存在说明设备入口已经建立，目标 TA 能否找到、命令能否成功，还要分别检查后续返回值。

## probe 发生在初始化阶段

这组源码固定到 manifest 4.10.0 选定的 [Linux 提交](https://github.com/linaro-swg/linux/tree/cf6e3218c25183cbc45551e85d0dd531f00fcc3d)。采用传统 SMC ABI 时，OP-TEE 的平台驱动定义和 `optee_probe` 在 `smc_abi.c` 中。

设备与驱动匹配后，probe 在建立绑定的过程中完成初始化：选定通信 conduit、查询安全侧的接口能力、准备共享内存等资源，并注册普通客户端与 supplicant 使用的 TEE 设备。虽然实现位于 `smc_abi.c`，conduit 仍会依据设备属性选择 SMC 或 HVC。本系列的 QEMU 配置使用 SMC。[SMC ABI 的初始化实现](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/smc_abi.c)

这些准备工作完成后，运行期请求才会沿设备回调分发，应用每发一个 Command 不会重新执行 probe。排查初始化失败时，要看启动日志和能力协商；设备已经可用、TA 返回参数错误时，则应继续追对应的请求处理函数。

## tee_fops 与 TEE 操作表

Linux 把字符设备的操作连接到 `file_operations`。在这里，通用 TEE core 定义 `tee_fops`，其中 `.open` 对应 `tee_open`，`.unlocked_ioctl` 对应 `tee_ioctl`。

打开设备时建立 TEE context，并通过文件的私有数据关联后续请求。应用调用 ioctl 后，`tee_ioctl` 取出这个 context，根据 ioctl 编号继续分发。`TEE_IOC_OPEN_SESSION` 进入打开会话处理，`TEE_IOC_INVOKE` 进入命令处理，关闭会话、共享内存等各有入口。[TEE core 的设备与 ioctl 实现](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/tee_core.c)

从 `tee_ioctl` 继续往下，还有一张 TEE 驱动操作表。通用层检查用户缓冲区和参数数量、转换参数，之后通过 `ops->open_session` 或 `ops->invoke_func` 等接口交给具体驱动。OP-TEE 将这两个入口分别连接到 `optee_open_session`、`optee_invoke_func`。它们与字符设备的 `file_operations` 分属两层。

TEE core 负责 Linux 用户接口，OP-TEE 驱动负责具体的消息和通信协议。通用层检查接口结构是否合理，hello_world 命令允许什么输入则由 TA 检查。

![用户态 ioctl 经 TEE core 和 OP-TEE 驱动进入安全侧](/post/tee-03-linux-tee-driver/architecture.svg)

## 从 ioctl 参数到 OP-TEE 消息

以 InvokeCommand 为例，CA 交给 libteec 的是 Session、Command 和 operation。libteec 准备 `tee_ioctl_invoke_arg` 与参数数组，再用 `tee_ioctl_buf_data` 描述这一段用户态缓冲区，调用 `TEE_IOC_INVOKE`。定义可以在固定版本的 [TEE UAPI 头文件](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/include/uapi/linux/tee.h)中对照。

内核需要检查用户给出的指针和长度。TEE core 通过用户内存访问接口复制请求，检查参数属性、处理共享内存引用，再调用具体驱动。读代码时除了 `copy_from_user`，还要留意 value 和 memref 的处理分支：memref 关联着已经注册或分配的共享内存对象。

OP-TEE 的 `call.c` 准备消息，把 session、命令及参数转换成安全侧 ABI 使用的形式，然后经 `do_call_with_arg` 发送。传统路径的实现位于 `smc_abi.c`；同一驱动也有 FF-A 路径，沿代码跳转时要看操作表到底绑定到哪套实现。[请求转换实现](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/call.c)

下面是一张定位用的调用草图，省略了校验、取消、资源回收等分支，不是逐行等价的程序：

```text
libteec: InvokeCommand
  → ioctl(TEE_IOC_INVOKE)
  → tee_ioctl → tee_ioctl_invoke
  → ops->invoke_func → optee_invoke_func
  → do_call_with_arg → optee_smc_do_call_with_arg
  → 已选择的 conduit → Secure Monitor → OP-TEE
```

最下面使用哪个 SMC 功能号，取决于消息内存和能力协商结果。该版本可能使用 `CALL_WITH_ARG`、`CALL_WITH_RPC_ARG` 或 `CALL_WITH_REGD_ARG`，都属于这里讨论的传统消息调用路径，参数携带方式有所不同。

## ioctl 返回 0，TA 就一定成功了吗

这里需要分别看 Linux 系统调用的返回值和 TA 的业务返回值。

ioctl 可以成功完成数据传递，同时在返回结构中带回 TA 的错误，例如参数类型不对。libteec 读取这个返回值与 origin，再向 CA 报告。所以 strace 最右边的 `= 0` 只说明系统调用成功，还要继续看结构体中的结果。

反过来，系统调用失败，例如用户地址无法访问，可能还没走到 TA。这时应该同时记录 syscall 返回、`TEEC_Result` 和错误来源。对于 memref，输出长度也是结果的一部分。第四篇会用短缓冲区把这个区别实际表现出来。

## 对照 hello_world 的 strace

实验沿用第一篇的 [9 月 18 日 CI 运行 35257180558](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558)，直接追官方 hello_world，不修改它的业务代码。[固定版本运行脚本](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/run-qemu.py)先记录来宾内核、设备节点及工具位置，再执行下面的跟踪。构建阶段已通过 `BR2_PACKAGE_STRACE=y` 选入工具，无须在来宾里临时安装软件。

```sh
uname -a
ls -l /dev/tee*
command -v strace
strace -s 256 -e trace=openat,close,ioctl \
  -o /tmp/hello.strace optee_example_hello_world
lab_status=$?
printf '\n__LAB_STATUS=%s\n' "$lab_status"
```

这段命令跟踪的是来宾 Linux 的系统调用，不会直接显示 EL3 寄存器变化、SMC 指令执行或者 TA 内部调用栈。本次只选择打开文件、关闭文件和 ioctl 三类事件，用于确认设备节点及请求顺序，没有加入 mmap、时间戳或额外的文件描述符解码选项。运行脚本读取状态标记，并把来宾文件取回为 `evidence/hello-world.strace.txt`；应用输出和两路串口则单独保存。

实际来宾报告的内核是 `6.18.0-gcf6e3218c251`，与锁定的提交相符。[启动日志](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-normal.txt) 在应用运行前已有 `optee: revision 4.10 (753afbbee1682f5d)`、`dynamic shared memory is enabled` 和 `initialized driver`，对应前面说的驱动初始化阶段。

[完整 strace](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/hello-world.strace.txt) 中，设备打开与能力查询两行是：

```text
openat(AT_FDCWD, "/dev/tee0", O_RDWR)   = 3
ioctl(3, TEE_IOC_VERSION, {impl_id=TEE_IMPL_ID_OPTEE, gen_caps=TEE_GEN_CAP_GP|TEE_GEN_CAP_REG_MEM|TEE_GEN_CAP_MEMREF_NULL, impl_caps=TEE_OPTEE_CAP_TZ}) = 0
```

后续 TEE 请求都使用文件描述符 3。能力查询返回了注册内存支持，但这次加一实际传的是 value。下面摘出后续请求中的主要字段，完整结构见原始 trace：

| 请求 | 本次输入和返回 |
| --- | --- |
| `TEE_IOC_OPEN_SESSION` | UUID 为 hello_world 的 `8aaaf200-2450-11e4-abe2-0002a5d5c51b`，公开登录，返回 `session=0x2`、`ret=0` |
| `TEE_IOC_INVOKE` | `func=0`、`session=0x2`，第一个参数为 VALUE_INOUT，`a=0x2a` 返回为 `0x2b` |
| 命令结果 | `ret=0`，`ret_origin=TEEC_ORIGIN_TRUSTED_APP`，系统调用自身也返回 0 |
| `TEE_IOC_CLOSE_SESSION` | 关闭 `session=0x2`，返回 0 |
| `close(3)` | 关闭设备描述符，进程最终 `exited with 0` |

`0x2a` 和 `0x2b` 就是 42、43，这与第一篇两侧日志里的数字一致。此次 CA 的 trace 没有 `TEE_IOC_SHM_REGISTER` 或 `TEE_IOC_SHM_ALLOC`；它使用 value 参数，这是实际请求选择的路径，并不否定驱动内部需要消息内存。

trace 中间还出现了对描述符 1 的 `TCGETS`，这是终端相关 ioctl。筛选 TEE 请求时，需要同时核对文件描述符和请求编号。

如果 strace 版本不能解码 TEE 请求，可以保留原始 ioctl 数值，对照同版本 UAPI 查定义，不能直接将这些数值当作 SMC 功能号。CA 的 trace 里没有 TA 文件加载记录，因为读取文件的是另一个进程 tee-supplicant。实验脚本对它另行附加跟踪，第五篇继续看；给当前命令加上 `-f`，也不会自动跟踪系统里所有既有进程。

源码链接均固定到 manifest 4.10.0 对应组件提交；[本次构建配置](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/build-config.txt)记录了 `SPMC_AT_EL=n` 与 `SPD=opteed`。本文的系统调用顺序来自 strace，内核函数之间的调用关系来自固定源码；这次没有对内核调用栈或 SMC 指令逐步跟踪。

系列目录：[01 调用链](/post/tee-01-ca-to-ta.html) · [02 ARMv8 异常级](/post/tee-02-armv8-exception-levels.html) · [03 Linux 驱动](/post/tee-03-linux-tee-driver.html) · [04 共享内存](/post/tee-04-shared-memory.html) · [05 RPC](/post/tee-05-rpc-and-supplicant.html) · [06 启动过程](/post/tee-06-before-the-first-call.html)

上一篇：[看 TEE 代码之前，我先把 ARMv8 的异常级理清了](/post/tee-02-armv8-exception-levels.html)。下一篇：[传给 TA 的参数，为什么不能只是一个指针？](/post/tee-04-shared-memory.html)。
