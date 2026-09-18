---
title: TA 还没执行完，为什么又回到了 Linux？
date: "2026-09-15T08:00:00+08:00"
updated: "2026-09-18T08:54:38+08:00"
tags: [TEE, OP-TEE, Linux, RPC, TrustZone]
categories: [系统安全]
description: 从一次 REE 文件系统用户 TA 的加载请求，理解 OP-TEE trusted thread、RPC、tee-supplicant 与尚未结束的客户端调用。
series: 顺着一次 TEE 调用
series_order: 5
permalink: /post/tee-05-rpc-and-supplicant.html
---

第一篇的调用图省掉了一些来回。比如打开 hello_world 的 Session 时，TA 文件还在 Linux 的文件系统里。OP-TEE 得先取到这份文件，才能继续装载。这时 CA 还在等 OpenSession 返回，CPU 却已经回到 Linux 做事了。

这里用到了 RPC：安全侧发出请求，由普通世界协助处理，等结果回来后继续执行。这样 OP-TEE 就能借用已有的文件服务，无须再实现 Linux 的文件系统和存储驱动。

RPC 全称是 Remote Procedure Call。这篇里的请求和响应都发生在同一台机器上，跨的是安全世界与普通世界。

## 回来了，但客户端还没拿到结果

传统 SMC 路径中，OP-TEE 对可能挂起、恢复的服务使用 yielding call。普通世界进入安全侧之后，OP-TEE 为请求安排 trusted thread，保存执行所需的状态。请求需要普通世界服务时，可以暂停这一线程，通过 Monitor 把控制权交回去，服务完成后再恢复。[OP-TEE trusted thread 说明](https://optee.readthedocs.io/en/4.10.0/architecture/core.html#trusted-thread-scheduling)

trusted thread 是 OP-TEE 管理的执行上下文，在 Linux 里用 `ps` 找不到它。恢复执行时仍然需要普通世界调用线程的配合，不能直接套用 Linux 进程和调度器的概念。

Linux 驱动通过安全侧返回的状态区分这两种情况。看固定版本的 `optee_smc_do_call_with_arg`，会发现调用外面套着一层循环：遇到 RPC 返回就先处理 RPC，再带着结果重新进入 OP-TEE；等到最终返回，才离开循环。[Linux SMC 调用循环](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/smc_abi.c)

只保留这几个分支，流程如下。驱动中还有线程资源不足、取消和清理等处理，这里暂时省略：

```text
首次进入 OP-TEE，获得返回状态
  ├─ RPC：普通世界处理请求
  │       → 以 RETURN_FROM_RPC 再次进入 OP-TEE
  │       → 继续判断下一次返回状态
  └─ 完成：结束驱动调用，向上返回
```

在这段往返期间，同一个 CA 线程可能一直等在 `TEEC_OpenSession` 或 `TEEC_InvokeCommand` 内，libteec 还没有向应用返回结果。一次接口调用可以经过多次 SMC，数 SMC 的次数不能直接当作业务调用次数。

## tee-supplicant 是谁叫来的

普通客户端通常使用 `/dev/teeN`，tee-supplicant 使用特权设备 `/dev/teeprivN`。它是普通世界中的用户态服务进程，负责处理分配给它的请求，比如读取 REE 文件系统中的 TA。[Linux TEE 设备接口](https://docs.kernel.org/userspace-api/tee.html)

安全侧的请求要经过 OP-TEE 的 RPC 返回、Linux 驱动和设备接口，才能到达这个进程。驱动把需要用户态协助的任务交给 supplicant；supplicant 通过 `TEE_IOC_SUPPL_RECV` 等待请求，处理完再用 `TEE_IOC_SUPPL_SEND` 交回结果。[supplicant 请求循环](https://github.com/OP-TEE/optee_client/blob/9f5e90918093c1d1cd264d8149081b64ab7ba672/tee-supplicant/src/tee_supplicant.c)

有些 RPC 到驱动这一层就能处理，例如读取时间、等待通知。需要用户态服务的类别才继续交给 supplicant。具体分流可以看 [`rpc.c`](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/rpc.c)，等待 supplicant 请求完成的逻辑在 [`supp.c`](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/supp.c)里。

查日志时还得确认这次回来要做什么：RPC 功能号是什么、哪个进程在处理、发生在调用的哪一步。中断、通知和其他服务也会影响执行顺序，不能看到返回 Linux 就认定是在读 TA 文件。

![REE 文件系统 TA 加载时的 RPC 往返与安全侧校验](/post/tee-05-rpc-and-supplicant/architecture.svg)

## 先问大小，再取文件

这次看的是 REE filesystem user TA。`.ta` 文件通常以 UUID 命名，存放在 supplicant 配置的搜索目录里。实际从哪个目录找，由构建配置和启动参数决定；实验里的 `/lib` 路径并非协议规定。

打开目标 Session、需要加载 TA 时，安全侧会沿加载路径找到相应的存储后端。固定版本的 `ree_fs_ta.c` 中，`rpc_load` 先用 `OPTEE_RPC_CMD_LOAD_TA` 询问大小，再申请合适的共享缓冲区，随后请求文件内容。中间还可能有共享内存相关 RPC，所以一次 TA 加载会包含多次请求。[REE TA 加载与验证实现](https://github.com/OP-TEE/optee_os/blob/753afbbee1682f5d16fd30e87b31058a4fd4f4b8/core/kernel/ree_fs_ta.c)

supplicant 接到 LOAD_TA 请求，根据 UUID 查找文件，把内容放到约定的缓冲区，再返回长度与结果。文件取回来之后，安全侧还要检查签名头、边界、UUID 等条件，验证装载内容的完整性；启用加密格式时，还会进行相应的解密验证。

TA 文件可以保存在普通世界，接受它的条件由安全侧校验，supplicant 无权决定任意字节都能作为可信代码执行。签名验证也没有让文件内容变得保密：未加密的 TA 文件仍可能被普通世界读取。

这条路径仍然依赖普通世界及时响应。文件被删了、supplicant 没运行，或者普通世界一直不返回，调用就可能无法完成。内容认证解决不了这些可用性问题。

## 哪些调用会碰到加载

用户 TA 可以来自不同存储位置。early TA 的内容随 OP-TEE 镜像携带，因此加载它不需要走本文这条“从 REE 文件系统取文件”的路径；pseudo TA 则直接编入 OP-TEE core，运行层级和接口实现也不同。[OP-TEE 的 TA 类型与位置](https://optee.readthedocs.io/en/4.10.0/architecture/trusted_applications.html)

对于 REE 用户 TA，已有 Session 中再次执行纯计算命令，通常也无须重新装载应用文件。LOAD_TA 不会固定地跟着每次 InvokeCommand 发生，其他 RPC 则取决于实际服务、配置和运行情况。

但关闭 CA 再启动一次，就要看 TA 的实例和存活策略了。固定版本的 hello_world 使用 `TA_FLAGS=0`，没有设置成 keep-alive 的单实例 TA。关闭会话再重开，与同一实例内再次调用是两种情况，因此不能断定第二次启动 CA 就不会加载文件。[hello_world 的 TA 属性](https://github.com/linaro-swg/optee_examples/blob/934c7edb74a26e90f68024cf441073528444177f/hello_world/ta/user_ta_header_defines.h)

## 在日志里对应起来

这里与前三篇共用 [9 月 18 日 CI 运行 35257180558](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558) 的 QEMU 镜像。[本次运行脚本](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/run-qemu.py)先登录来宾，找到 init 脚本已经启动的 tee-supplicant，然后用 `-p` 附加到现有进程。实际主进程 PID 为 105，跟踪中又附加到线程 151、152，记录保存在 [supplicant-attach.txt](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/supplicant-attach.txt)。

下面保留来宾中的主要跟踪步骤，完整脚本还会检查 tracer 是否退出，并收集输出和状态：

```sh
strace -f -s 256 -e trace=openat,read,close,ioctl \
  -o /tmp/supplicant.strace -p $(pidof tee-supplicant) \
  2>/tmp/supplicant-attach.txt &
SERIES_TRACER=$!
sleep 1
kill -0 $SERIES_TRACER

strace -s 256 -e trace=openat,close,ioctl \
  -o /tmp/hello.strace optee_example_hello_world
optee_series_echo

kill -INT $SERIES_TRACER
sleep 1
```

Buildroot 镜像包含 strace，这些命令以来宾 root 执行。运行脚本检查各步的退出状态，先附加跟踪，再运行未修改的 hello_world 和本系列的 echo 示例，结束时向 tracer 发送 SIGINT，取回 trace、附加诊断与两侧串口记录。文件由 supplicant 读取，所以这部分要看它的 trace，CA 的 trace 里找不到。

我先用 hello_world 的 UUID 找到了下面两次成功的文件打开。[原始 trace](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/supplicant.strace.txt) 中两行之间还有 ioctl、read 等操作，这里用省略号略去：

```text
151   openat(AT_FDCWD, "/lib/optee_armtz/8aaaf200-2450-11e4-abe2-0002a5d5c51b.ta", O_RDONLY) = 6
...
151   openat(AT_FDCWD, "/lib/optee_armtz/8aaaf200-2450-11e4-abe2-0002a5d5c51b.ta", O_RDONLY) = 7
```

把两次 open 前后的参数也带上，就能对到源码里的步骤。第一次请求的输出 memref 大小为 0，supplicant 回应 `size=0x1be28`；接着是长度为 `0x1be28` 的 `TEE_IOC_SHM_REGISTER`，成功得到共享内存 ID 2。下一次同 UUID 请求携带这个大小和 `shm_id=2`，随后才有第二次打开文件、读取内容，以及 `TEE_IOC_SUPPL_SEND` 的成功回应。顺序正好是询问大小、准备缓冲区、取得内容。

再到安全侧查同一个 UUID，可以找到 [UART 中相邻的两行](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-secure.txt)：

```text
D/TC:? 0 ldelf_syscall_open_bin:163 Lookup user TA ELF 8aaaf200-2450-11e4-abe2-0002a5d5c51b (REE)
D/TC:? 0 ldelf_syscall_open_bin:167 res=0
```

后面接着是该 UUID 的 ELF 装载、TA 创建、`Hello World!`，以及把 42 加到 43 的日志。CA 这边的 OpenSession、Invoke 也都成功，程序退出码为 0。文件读取之后确实继续完成了装载和调用。

我还注意到，同一 UUID 前面已经出现过 `Lookup pseudo TA`、`early TA` 和 `Secure Storage TA`。early TA 和 Secure Storage TA 的查找都返回了 `0xffff0008`，随后才在 REE 找到。这里的 `Lookup` 只是查找尝试，要连着返回值看，才能知道最后用了哪个来源。

echo 的 UUID `4d5acb20-46c2-4bc7-9c0d-58f50a1179d2` 也出现在 `/lib/optee_armtz/` 的成功打开记录中，安全侧有对应的 REE 查找成功与 ELF 装载。它在同一个 Session 内执行五项检查，最终输出 [`PASS: 5 cases`](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/echo-tests.txt)。这次可以确认两个应用都经过了文件获取并继续执行，但还不能据此给每个 Command 标上精确的 RPC 次数。

这份 trace 只能看到普通世界接口，没有逐条记录 SMC 的进入、返回和寄存器变化。暂停 trusted thread、通过 `RETURN_FROM_RPC` 恢复的过程，还需要沿固定源码去看。本次日志直接留下的是文件请求、共享内存参数，以及后续的 TA 执行记录。

以上都基于传统 SMC ABI。FF-A 的通信和共享内存路径不同，这里的返回寄存器约定不能直接套过去。下一篇回到启动过程，看看 OP-TEE 自己是怎么被加载起来的。

系列目录：[01 调用链](/post/tee-01-ca-to-ta.html) · [02 ARMv8 异常级](/post/tee-02-armv8-exception-levels.html) · [03 Linux 驱动](/post/tee-03-linux-tee-driver.html) · [04 共享内存](/post/tee-04-shared-memory.html) · [05 RPC](/post/tee-05-rpc-and-supplicant.html) · [06 启动过程](/post/tee-06-before-the-first-call.html)

上一篇：[传给 TA 的参数，为什么不能只是一个指针？](/post/tee-04-shared-memory.html)。下一篇：[能调用 TA 之前，系统是怎样启动起来的？](/post/tee-06-before-the-first-call.html)。
