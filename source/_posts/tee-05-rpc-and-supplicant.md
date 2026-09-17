---
title: TA 还没执行完，为什么又回到了 Linux？
date: "2026-09-18T03:20:08+08:00"
tags: [TEE, OP-TEE, Linux, RPC, TrustZone]
categories: [系统安全]
description: 从一次 REE 文件系统用户 TA 的加载请求，理解 OP-TEE trusted thread、RPC、tee-supplicant 与尚未结束的客户端调用。
series: 顺着一次 TEE 调用
series_order: 5
permalink: /post/tee-05-rpc-and-supplicant.html
---

第一篇把请求画成了从 CA 一路进入 TA，再原路返回。为了认清参与者，这样画很方便，但只看这张图，容易形成另一个印象：安全侧必须把事情做完，才能回到 Linux。

实际没有这个要求。

例如，要打开的用户 TA 存放在普通世界的文件系统里。OP-TEE 需要拿到文件，却没有必要为了这一步把 Linux 的整套文件系统和存储驱动再实现一遍。它可以把请求交给普通世界，等数据送回来之后接着执行。

这就是这里要看的 RPC。虽然也叫 Remote Procedure Call，但本文讨论的是同一台机器内，安全侧请求普通世界协助完成工作的机制，不是突然多了一台远程服务器。

## 回来了，但客户端还没拿到结果

传统 SMC 路径中，OP-TEE 对可能挂起、恢复的服务使用 yielding call。普通世界进入安全侧之后，OP-TEE 为请求安排 trusted thread，保存执行所需的状态。请求需要普通世界服务时，可以暂停这一线程，通过 Monitor 把控制权交回去，服务完成后再恢复。[OP-TEE trusted thread 说明](https://optee.readthedocs.io/en/4.10.0/architecture/core.html#trusted-thread-scheduling)

trusted thread 是 OP-TEE 管理的执行上下文，不是 Linux 中能用 `ps` 找到的一个新进程。它的恢复又与普通世界调用线程的执行有关，所以也不能按“安全世界里另有一套完全独立的 Linux 调度器”来理解。

Linux 驱动怎么知道这次是暂停还是结束？它检查安全侧返回的状态。在固定版本的 `optee_smc_do_call_with_arg` 中，调用周围存在循环：遇到 RPC 返回，先处理 RPC，再带着相应信息重新进入 OP-TEE；遇到最终返回才离开这一轮处理。[Linux SMC 调用循环](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/smc_abi.c)

可以把关键分支压缩成下面的阅读草图。它省略了线程资源不足、取消和清理等处理，不能拿去替代驱动实现：

```text
首次进入 OP-TEE，获得返回状态
  ├─ RPC：普通世界处理请求
  │       → 以 RETURN_FROM_RPC 再次进入 OP-TEE
  │       → 继续判断下一次返回状态
  └─ 完成：结束驱动调用，向上返回
```

因而，同一个 CA 线程可能仍然卡在 `TEEC_OpenSession` 或 `TEEC_InvokeCommand` 内。CPU 已经回过普通世界，不等于 libteec 已经把结果交给应用。排查时如果只数“出现了几次 SMC”，很容易把中途服务当成几次独立业务调用。

## tee-supplicant 是谁叫来的

普通客户端通常使用 `/dev/teeN`，tee-supplicant 使用特权设备 `/dev/teeprivN`。它是普通世界中的用户态服务进程，负责处理分配给它的请求，比如读取 REE 文件系统中的 TA。[Linux TEE 设备接口](https://docs.kernel.org/userspace-api/tee.html)

它没有被 TA 直接调用成一个普通 C 函数。中间仍然是 OP-TEE 的 RPC 返回、Linux 驱动和设备接口：驱动把需要用户态协助的任务交给 supplicant；supplicant 通过 `TEE_IOC_SUPPL_RECV` 等待请求，处理完再用 `TEE_IOC_SUPPL_SEND` 交回结果。[supplicant 请求循环](https://github.com/OP-TEE/optee_client/blob/9f5e90918093c1d1cd264d8149081b64ab7ba672/tee-supplicant/src/tee_supplicant.c)

但 RPC 也不是 tee-supplicant 的同义词。驱动可以直接处理部分 RPC，例如读取时间、等待通知等；只有需要用户态服务的类别才继续交给 supplicant。这一处分流在 [`rpc.c`](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/rpc.c)里，而等待 supplicant 请求完成的配合逻辑在 [`supp.c`](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/supp.c)里。

所以，只看到安全侧返回 Linux，不能直接推断它在读 TA 文件。需要把 RPC 功能号、对应进程活动和请求时间对起来。中断、通知以及其他服务，也可能让执行路径不再是一条直线。

![REE 文件系统 TA 加载时的 RPC 往返与安全侧校验](/post/tee-05-rpc-and-supplicant/architecture.svg)

## 一次 TA 加载，可能不止一个请求

这里选的是 REE filesystem user TA。`.ta` 文件通常以 UUID 命名，存放在 supplicant 配置的搜索目录里。具体目录要看构建配置和启动参数，不把某个发行版的 `/lib` 路径当成协议规定。

打开目标 Session、需要加载这个 TA 时，安全侧会沿 TA 加载路径找到相应存储后端。固定版本的 `ree_fs_ta.c` 中，`rpc_load` 先用 `OPTEE_RPC_CMD_LOAD_TA` 询问大小，再申请合适的共享缓冲区，并继续请求文件内容。中间还可能涉及共享内存相关 RPC。光从这里就能看出，“加载一个 TA”不等于“刚好一次 RPC”。[REE TA 加载与验证实现](https://github.com/OP-TEE/optee_os/blob/753afbbee1682f5d16fd30e87b31058a4fd4f4b8/core/kernel/ree_fs_ta.c)

supplicant 接到 LOAD_TA 请求，根据 UUID 查找文件，把内容放到约定的缓冲区，并返回长度与结果。它负责取文件，不负责宣布这个文件值得信任。安全侧仍要检查签名头、边界、UUID 等条件，并验证装载内容的完整性；启用加密格式时还有对应的解密验证处理。

这里我最想分清的是两件事：文件从哪里取，和凭什么执行。文件可以放在普通世界，不表示普通世界有权决定任意字节都能变成可信代码。签名验证也不自动提供文件内容的保密性，未加密的 TA 文件仍可能被普通世界读取。

同样，使用普通世界的服务，也就依赖它在需要时提供响应。文件被删了、supplicant 没运行、普通世界一直不返回，正常服务就可能无法完成。安全侧对内容做认证，不能顺手把这些可用性问题也解决掉。

## 不要拿这个例子覆盖所有 TA

用户 TA 可以来自不同存储位置。early TA 的内容随 OP-TEE 镜像携带，因此加载它不需要走本文这条“从 REE 文件系统取文件”的路径；pseudo TA 则直接编入 OP-TEE core，运行层级和接口实现也不同。[OP-TEE 的 TA 类型与位置](https://optee.readthedocs.io/en/4.10.0/architecture/trusted_applications.html)

即使都是 REE 用户 TA，也不能说每次 InvokeCommand 必然发生一次 LOAD_TA。已有 Session 中再次执行纯计算命令，通常没有重新装载应用文件的理由；是否出现其他 RPC，要看实际服务、配置及运行情况。

另一个容易写错的实验结论是“第二次启动 CA 必然不会再加载”。这涉及 TA 的实例和存活策略。固定版本的 hello_world 使用 `TA_FLAGS=0`，不是特意设置成 keep-alive 的单实例 TA。关闭会话再重开，不能被当作“同一实例内再次调用”的等价实验。[hello_world 的 TA 属性](https://github.com/linaro-swg/optee_examples/blob/934c7edb74a26e90f68024cf441073528444177f/hello_world/ta/user_ta_header_defines.h)

## 顺着真实记录找一次加载

这里与前三篇共用 [CI 运行 35257180558](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558) 的 QEMU 镜像。[本次运行脚本](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/run-qemu.py)先登录来宾，找到 init 脚本已经启动的 tee-supplicant，然后用 `-p` 附加到现有进程。实际主进程 PID 为 105，跟踪中又附加到线程 151、152，记录保存在 [supplicant-attach.txt](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/supplicant-attach.txt)。

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

Buildroot 镜像包含 strace，自动化以来宾 root 执行，并为各步检查退出状态。先附加，再运行未修改的 hello_world 和本系列的 echo 示例，结束时向 tracer 发送 SIGINT，取回 trace、附加诊断与两侧串口记录。只读 CA 的 trace 看不到另一个进程的文件操作，单独跟踪 supplicant 才能补上这一段。

我先用 hello_world 的 UUID 找到了下面两次成功的文件打开。[原始 trace](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/supplicant.strace.txt) 中两行之间还有 ioctl、read 等操作，这里用省略号略去：

```text
151   openat(AT_FDCWD, "/lib/optee_armtz/8aaaf200-2450-11e4-abe2-0002a5d5c51b.ta", O_RDONLY) = 6
...
151   openat(AT_FDCWD, "/lib/optee_armtz/8aaaf200-2450-11e4-abe2-0002a5d5c51b.ta", O_RDONLY) = 7
```

这里值得继续看的不是“两次”这个数字，而是它们前后的参数。第一次对应请求的输出 memref 大小为 0，supplicant 回应时给出了 `size=0x1be28`；随后出现长度为 `0x1be28` 的 `TEE_IOC_SHM_REGISTER`，成功得到共享内存 ID 2。下一次同 UUID 请求携带这个大小和 `shm_id=2`，之后才有第二次文件打开、内容读取及 `TEE_IOC_SUPPL_SEND` 的成功回应。这些字段与前面源码中的“询问大小、准备缓冲区、取得内容”相符。

安全侧的记录补上了后半段。下面是 [UART 中相邻的两行](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-secure.txt)：

```text
D/TC:? 0 ldelf_syscall_open_bin:163 Lookup user TA ELF 8aaaf200-2450-11e4-abe2-0002a5d5c51b (REE)
D/TC:? 0 ldelf_syscall_open_bin:167 res=0
```

再往后可以看到该 UUID 的 ELF 装载、TA 创建、`Hello World!`，以及把 42 加到 43 的日志。对应 CA 的 OpenSession、Invoke 都成功，程序退出码为 0。这样就不是单凭一行文件打开，宣称整个加载和调用都完成了。

日志里还有个很容易误读的地方：同一 UUID 之前也出现过 `Lookup pseudo TA`、`early TA` 和 `Secure Storage TA`。其中两种用户 TA 存储的查找返回了 `0xffff0008`，随后才在 REE 找到。`Lookup` 记录的是尝试，不是“这个应用同时属于所有类型”；判定加载来源要连着返回结果看。

echo 的 UUID `4d5acb20-46c2-4bc7-9c0d-58f50a1179d2` 也出现在 `/lib/optee_armtz/` 的成功打开记录中，安全侧有对应的 REE 查找成功与 ELF 装载。它在同一个 Session 内执行五项检查，最终输出 [`PASS: 5 cases`](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/echo-tests.txt)。这次可以确认两个应用都经过了文件获取并继续执行，但还不能据此给每个 Command 标上精确的 RPC 次数。

这份 trace 观察的是普通世界接口；它没有逐条记录 SMC 的进入、返回或寄存器变化。暂停 trusted thread、`RETURN_FROM_RPC` 恢复的机制由固定源码解释，文件请求、共享内存参数和后续 TA 执行则有本次日志相互印证。把两种材料放在一起，往返过程就有了依据，也不用假装一份 strace 能看穿所有层。

本文固定使用传统 SMC ABI；FF-A 的通信与共享内存路径需要另行分析，不能照抄这里的返回寄存器约定。接下来再往前倒一点：能进入 OP-TEE、能验证 TA 之前，OP-TEE 自己又是怎么被加载起来的？

系列目录：[01 调用链](/post/tee-01-ca-to-ta.html) · [02 ARMv8 异常级](/post/tee-02-armv8-exception-levels.html) · [03 Linux 驱动](/post/tee-03-linux-tee-driver.html) · [04 共享内存](/post/tee-04-shared-memory.html) · [05 RPC](/post/tee-05-rpc-and-supplicant.html) · [06 启动过程](/post/tee-06-before-the-first-call.html)

上一篇：[传给 TA 的参数，为什么不能只是一个指针？](/post/tee-04-shared-memory.html)。下一篇：[能调用 TA 之前，系统是怎样启动起来的？](/post/tee-06-before-the-first-call.html)。
