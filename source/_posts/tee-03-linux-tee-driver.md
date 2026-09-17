---
title: 从 /dev/tee0 开始，追一次请求进入内核
date: "2026-09-18T03:20:06+08:00"
tags: [Linux, Kernel, Driver, TEE, OP-TEE]
categories: [系统安全]
description: 沿着 libteec 的 ioctl 请求，分清 TEE core 与 OP-TEE 驱动的职责，也把 probe 和运行期调用放回各自的位置。
series: 顺着一次 TEE 调用
series_order: 3
permalink: /post/tee-03-linux-tee-driver.html
---

前两篇把调用链和异常级放在了一起。现在往中间那根箭头里钻一点：CA 调用了 libteec，Linux 驱动怎么就接住了？

这次读驱动代码，我想先弄清一个容易让人打结的地方：`probe`、`file_operations`、`ioctl` 单独看都有各自的职责，但一层层函数指针连起来，很容易把它们都当成了“处理请求”。实际却不在同一个时间发生。

这次先盯住 hello_world 的一次加一，把两个问题分开：系统怎么准备好这个入口，以及应用运行时怎么使用这个入口。

## 设备文件不是 TA 的文件

普通应用通过 `/dev/teeN` 使用 Linux TEE 用户接口，tee-supplicant 则通过 `/dev/teeprivN` 接收需要普通世界协助处理的请求。`N` 是注册得到的编号，不能在所有系统上都认定为 0；CA 也不是拿 `/dev/tee0` 作为 TA 文件去读。[Linux TEE 用户接口说明](https://docs.kernel.org/userspace-api/tee.html)

当前 libteec 初始化 Context 时，会尝试设备节点，通过 `TEE_IOC_VERSION` 查询实现及能力，再判断是否符合要求。应用后续使用的是打开节点得到的文件描述符，目标 TA 的 UUID 放在会话请求里。这样，设备选择和应用选择就分开了。[libteec 的设备发现逻辑](https://github.com/OP-TEE/optee_client/blob/9f5e90918093c1d1cd264d8149081b64ab7ba672/libteec/src/tee_client_api.c)

这次来宾中实际出现的是 `/dev/tee0` 和 `/dev/teepriv0`，后面的跟踪也确实打开了前者。不过，看到设备文件存在，只能说明相应入口已经建立，不能说明目标 TA 一定存在，更不能说明业务调用一定成功。

## 先让驱动有地方站，再谈应用请求

这组源码固定到 manifest 4.10.0 选定的 [Linux 提交](https://github.com/linaro-swg/linux/tree/cf6e3218c25183cbc45551e85d0dd531f00fcc3d)。采用传统 SMC ABI 时，OP-TEE 的平台驱动定义和 `optee_probe` 在 `smc_abi.c` 中。

设备与驱动匹配后，probe 在建立绑定的过程中完成初始化。驱动需要选定通信 conduit、查询安全侧的接口能力、准备共享内存等资源，注册普通客户端与 supplicant 使用的 TEE 设备。这里的 conduit 会依据设备属性选择 SMC 或 HVC，不能看到文件名包含 `smc`，就认为所有机器都会直接执行同一种指令。本系列的 QEMU 配置使用 SMC。[SMC ABI 的初始化实现](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/smc_abi.c)

应用每发一个 Command，并不会重新调用一遍 probe。把 probe 放在每次调用的箭头中间，就像画 HTTP 请求流程时，每个请求先安装一次网卡，当然越画越复杂。

初始化完成之后，设备入口与回调关系已经在那里。运行期请求沿着这套关系分发。至于首次初始化为什么失败，应该看启动日志和能力协商；运行到一半某个 TA 返回参数错误，则是另一条排查线。

## file_operations 只负责接住第一棒

Linux 把字符设备的操作连接到 `file_operations`。在这里，通用 TEE core 定义 `tee_fops`，其中 `.open` 对应 `tee_open`，`.unlocked_ioctl` 对应 `tee_ioctl`。

打开设备时建立 TEE context，并通过文件的私有数据关联后续请求。应用调用 ioctl 后，`tee_ioctl` 取出这个 context，根据 ioctl 编号继续分发。`TEE_IOC_OPEN_SESSION` 进入打开会话处理，`TEE_IOC_INVOKE` 进入命令处理，关闭会话、共享内存等各有入口。[TEE core 的设备与 ioctl 实现](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/tee_core.c)

这里还有一层容易混淆：`file_operations` 不是 OP-TEE 自己的所有业务回调。TEE core 对下面的具体实现另有操作表。通用层检查用户缓冲区和参数数量、转换参数，之后通过 `ops->open_session` 或 `ops->invoke_func` 等接口交给具体驱动。OP-TEE 将这些入口连接到 `optee_open_session`、`optee_invoke_func`。

换句话说，TEE core 处理“Linux 用户态怎样使用 TEE 设备”，OP-TEE 驱动处理“怎样把这个请求表达成 OP-TEE 能理解的消息”。通用层能检查接口结构是否合理，但不了解 hello_world 的加一业务；这个命令到底允许几个输入，仍然要由 TA 检查。

![用户态 ioctl 经 TEE core 和 OP-TEE 驱动进入安全侧](/post/tee-03-linux-tee-driver/architecture.svg)

## 从 ioctl 参数到 OP-TEE 消息

拿 InvokeCommand 看，CA 交给 libteec 的是 Session、Command 和 operation。libteec 准备 `tee_ioctl_invoke_arg` 与参数数组，再用 `tee_ioctl_buf_data` 描述这一段用户态缓冲区，调用 `TEE_IOC_INVOKE`。定义可以在固定版本的 [TEE UAPI 头文件](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/include/uapi/linux/tee.h)中对照。

到内核以后，不能直接信任用户给出的指针和长度。TEE core 通过用户内存访问接口复制并检查请求，处理参数属性与共享内存引用，再调用具体驱动。这里并不是给所有参数简单套一个 `copy_from_user` 就结束了：value 和 memref 的含义不同，后者还关联已经注册或分配的共享内存对象。

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

也别把最下面写死为某一个 SMC 功能号。该版本根据消息内存和能力协商结果，可能使用 `CALL_WITH_ARG`、`CALL_WITH_RPC_ARG` 或 `CALL_WITH_REGD_ARG`。它们都属于这里讨论的传统消息调用路径，但参数携带方式不同。

## ioctl 返回 0，TA 就一定成功了吗

这是我读接口时会专门划出来的一点：Linux 系统调用的返回值和 TA 的业务返回值，不是同一层的结果。

假设 ioctl 成功完成了数据传递，但 TA 发现参数类型不对，它仍然可以在返回结构中填入错误。libteec 再读取这个返回值与 origin，向 CA 报告。因而只看到 strace 最右边的 `= 0`，不能宣布整个命令成功。

反过来，系统调用失败，例如用户地址无法访问，可能还没走到 TA。这时应该同时记录 syscall 返回、`TEEC_Result` 和错误来源。对于 memref，输出长度也是结果的一部分。第四篇会用短缓冲区把这个区别实际表现出来。

## 用 strace 给源码找一个落点

实验沿用第一篇的 [CI 运行 35257180558](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558)，直接追官方 hello_world，不修改它的业务代码。[固定版本运行脚本](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/run-qemu.py)先记录来宾内核、设备节点及工具位置，再执行下面的跟踪。构建阶段已通过 `BR2_PACKAGE_STRACE=y` 选入工具，无须在来宾里临时安装软件。

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

实际来宾报告的内核是 `6.18.0-gcf6e3218c251`，与锁定的提交相符。[启动日志](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-normal.txt) 在应用运行前已有 `optee: revision 4.10 (753afbbee1682f5d)`、`dynamic shared memory is enabled` 和 `initialized driver`。这是初始化阶段的观察，别和后面的命令执行混在一起。

[完整 strace](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/hello-world.strace.txt) 中，设备打开与能力查询两行是：

```text
openat(AT_FDCWD, "/dev/tee0", O_RDWR)   = 3
ioctl(3, TEE_IOC_VERSION, {impl_id=TEE_IMPL_ID_OPTEE, gen_caps=TEE_GEN_CAP_GP|TEE_GEN_CAP_REG_MEM|TEE_GEN_CAP_MEMREF_NULL, impl_caps=TEE_OPTEE_CAP_TZ}) = 0
```

文件描述符 3 把后续请求和这个设备接上了。能力位里出现注册内存支持，不表示这一次加一就一定用了 memref。把后续较长的结构体展开行整理成字段表，会更容易读：

| 请求 | 本次输入和返回 |
| --- | --- |
| `TEE_IOC_OPEN_SESSION` | UUID 为 hello_world 的 `8aaaf200-2450-11e4-abe2-0002a5d5c51b`，公开登录，返回 `session=0x2`、`ret=0` |
| `TEE_IOC_INVOKE` | `func=0`、`session=0x2`，第一个参数为 VALUE_INOUT，`a=0x2a` 返回为 `0x2b` |
| 命令结果 | `ret=0`，`ret_origin=TEEC_ORIGIN_TRUSTED_APP`，系统调用自身也返回 0 |
| `TEE_IOC_CLOSE_SESSION` | 关闭 `session=0x2`，返回 0 |
| `close(3)` | 关闭设备描述符，进程最终 `exited with 0` |

`0x2a` 和 `0x2b` 就是 42、43，这与第一篇两侧日志里的数字一致。此次 CA 的 trace 没有 `TEE_IOC_SHM_REGISTER` 或 `TEE_IOC_SHM_ALLOC`；它使用 value 参数，这是实际请求选择的路径，并不否定驱动内部需要消息内存。

这里也有一点小干扰：trace 中间出现了对描述符 1 的 `TCGETS`。那是终端相关 ioctl，不能因为名字里有 ioctl 就把它算进 TEE 调用链。先看文件描述符指向哪里，再看请求编号，往往比盯着整屏函数名有效。

如果 strace 版本不能解码 TEE 请求，先保留原始 ioctl 数值，再对照同版本 UAPI；不要给每个不认识的数随手贴个“SMC”的标签。没有看到 TA 的加载文件也不奇怪，读取文件的是另一个进程 tee-supplicant。实验脚本对它另行附加跟踪，第五篇继续看；即使给当前命令加上 `-f`，也不会自动跟踪系统里所有既有进程。

这条线追到这里，驱动已经不只是图上一个写着“Kernel”的方框了。下次找问题，可以先判断卡在设备初始化、用户接口转换、OP-TEE 消息提交，还是 TA 的命令处理，再决定往哪段代码里走。

源码链接均固定到 manifest 4.10.0 对应组件提交；[本次构建配置](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/build-config.txt)记录了 `SPMC_AT_EL=n` 与 `SPD=opteed`。系统调用顺序来自 strace，图中内核函数之间的连接来自这组源码，两份材料一起读，才能知道观察到的接口背后是谁在工作。

系列目录：[01 调用链](/post/tee-01-ca-to-ta.html) · [02 ARMv8 异常级](/post/tee-02-armv8-exception-levels.html) · [03 Linux 驱动](/post/tee-03-linux-tee-driver.html) · [04 共享内存](/post/tee-04-shared-memory.html) · [05 RPC](/post/tee-05-rpc-and-supplicant.html) · [06 启动过程](/post/tee-06-before-the-first-call.html)

上一篇：[看 TEE 代码之前，我先把 ARMv8 的异常级理清了](/post/tee-02-armv8-exception-levels.html)。下一篇：[传给 TA 的参数，为什么不能只是一个指针？](/post/tee-04-shared-memory.html)。
