---
title: TA 没返回，Linux 线程在等什么？
date: "2026-09-16T08:00:00+08:00"
updated: "2026-09-19T08:35:00+08:00"
tags: [Linux, OP-TEE, 并发]
categories: [系统安全]
description: 沿着 OP-TEE 驱动里的 supplicant 请求，看看队列锁何时释放、completion 在等谁，以及结果先回来为什么不会丢掉唤醒。
permalink: /post/linux-tee-wait-and-wakeup.html
---

第五篇追 TA 加载时，CA 还没从 `TEEC_OpenSession()` 返回，tee-supplicant 已经在读 `.ta` 文件了。读文件是这次调用的中间一步，安全侧完成后续装载和会话处理，CA 才能拿到 Session。

这期间两个 Linux 线程怎样配合，我还想往下看。调用线程在等文件，supplicant 要进驱动取请求，它们会不会被同一把锁挡住？如果文件很快就读完了，结果先回来，调用线程还没开始等，这次通知会不会丢？

沿着 RPC 往下读，会走到 Linux 的 `drivers/tee/optee/supp.c`。这段代码用 mutex 保护队列，用 completion 通知另一方继续执行。源码沿用前六篇的 [Linux 固定提交 `cf6e3218c251`](https://github.com/linaro-swg/linux/tree/cf6e3218c25183cbc45551e85d0dd531f00fcc3d)，仍然讨论传统 SMC 路径。

## 先分清是哪一个线程

CA 发出 ioctl 后，仍由这个 CA 线程沿着内核里的驱动调用栈往下走。进入内核这一步没有创建新的工作线程。

OP-TEE 请求普通世界协助时，控制权回到 Linux 驱动。需要 supplicant 处理的 RPC 会进入 `optee_supp_thrd_req()`，提交请求并等待结果。等在这里的就是进入驱动的调用线程；tee-supplicant 有自己的 Linux 线程，通过另一个设备接口接收请求。

安全侧还有 OP-TEE 管理的 trusted thread，它在 RPC 期间保存状态、暂停执行，等普通世界带着结果重新进入后再恢复。Linux 调用线程、supplicant 工作线程和安全侧 trusted thread 分属不同的执行环境，各有自己的调度和恢复过程。[OP-TEE 的线程调度说明](https://optee.readthedocs.io/en/4.10.0/architecture/core.html#trusted-thread-scheduling)

结果尚未就绪时，completion 的等待路径可以让当前 Linux 线程休眠，CPU 转去执行其他可运行线程。结果已经到了，等待就可以直接通过。仅凭“CA 还没返回”，还看不出它此刻是在执行、休眠，还是等待调度。

## 两个 completion，等的是两件事

`optee_supp_thrd_req()` 为一次请求分配 `struct optee_supp_req`，里面有功能号、参数指针、返回值，还有自己的 `struct completion c`。

同一份代码里还有一个 `supp->reqs_c`。名字相近，等待方却不同：

- `supp->reqs_c`：supplicant 的接收线程在这里等新请求。收到通知，就再去队列里取。
- `req->c`：提交这笔 RPC 的调用线程在这里等处理结果。请求完成，它才能继续。

`req` 保存参数指针和返回值，completion 则通知等待方何时可以继续。

下面摘出入队和等待之间的几行。此前已经分配请求、初始化 `req->c` 并填好参数；这里省略了内存分配失败和等待被中断后的分支：

```c
mutex_lock(&supp->mutex);
list_add_tail(&req->link, &supp->reqs);
req->in_queue = true;
mutex_unlock(&supp->mutex);

complete(&supp->reqs_c);

/* 接下来调用 wait_for_completion_killable(&req->c)，并检查返回值。 */
```

代码摘自 [`supp.c` 的请求提交路径](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/supp.c#L92-L130)，末行说明为本文添加；原文件由 Linaro 贡献，采用 GPL-2.0-only 许可。

提交侧持锁入队，随后就解锁。通知接收方、等待处理结果，都发生在解锁之后。

## 如果拿着锁等，会卡在哪里

supplicant 调用 `TEE_IOC_SUPPL_RECV` 进入 `optee_supp_recv()` 后，也要取得 `supp->mutex`，再从待处理队列中取请求。队列为空时，它先解锁，再等 `supp->reqs_c`；被通知后回到循环，重新检查队列。[接收路径](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/supp.c#L210-L269)

假设把提交侧的 `mutex_unlock()` 挪到等待结果之后，CA 线程就会拿着锁等 supplicant 处理；supplicant 却要先拿到这把锁，才能取走 CA 交来的请求。双方卡在这里，请求也就无法完成。

这里的 mutex 保护队列和请求登记等共享状态。等到 supplicant 在用户态读文件时，队列锁已经释放，其他请求仍有机会入队或被取走。

mutex 允许等待者休眠，在合适的上下文里，持锁期间也可以发生休眠。这段假设代码的问题在于依赖关系：等待的另一方也需要同一把锁。换成自旋锁仍然解不开这个依赖，而且这类可能休眠的等待接口不适用于原子上下文。[内核 mutex 语义](https://docs.kernel.org/locking/mutex-design.html#semantics)、[completion 的等待约束](https://docs.kernel.org/scheduler/completion.html#waiting-for-completions)

![一次 supplicant 请求中，队列锁与两次通知各自发生的位置](/post/linux-tee-wait-and-wakeup/wait-and-reply.svg)

## 结果先回来，会不会白通知一次

两个线程并行执行时，提交侧可能刚通知“有请求”，还没运行到等待结果，另一个 CPU 上的 supplicant 就已经处理完了。

completion 会保留完成状态。初始化后的 `done` 为 0；普通 `complete()` 增加完成计数，等待方检查到已有完成事件，就消费一次并继续，无须先睡下去。检查、登记等待和唤醒之间也有 completion 自己的同步机制，普通布尔变量并不具备这些语义。[completion 接口说明](https://docs.kernel.org/scheduler/completion.html#usage)

固定版本的 [`kernel/sched/completion.c`](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/kernel/sched/completion.c#L18-L118)也能对上这个过程：通知侧在内部锁保护下更新 `done`；等待侧仅在尚未完成时进入等待，继续前消费完成计数。这里讨论单次 `complete()` 的用法，`complete_all()` 和重新初始化还有各自的规则。

对 `supp->reqs_c` 来说，收到通知和取到请求还是两步。supplicant 从等待里回来后，要重新查队列，取出请求并登记请求 ID。通知本身并没有把某个请求分配给这个线程，后续回复仍要通过 ID 找到对应对象。

## 回复回来，还要回一次 OP-TEE

请求出队时，驱动会把它登记到 IDR，也就是按整数 ID 查找对象的映射中。支持 meta 参数的 supplicant 会拿到请求 ID，发送结果时再带回来。多个工作线程的回复，也由这个 ID 对应到各自的请求。

正常的 `optee_supp_send()` 路径先持锁查找并移除对应登记，然后解锁，回填输出参数和 `req->ret`，最后执行 `complete(&req->c)`。[回复路径](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/supp.c#L319-L362)

我读到这里时，多看了一眼回填和通知的顺序。正常完成后，等待方就可以读取返回值，随后释放请求对象，所以发送方先准备好结果，再调用 `complete()`，之后也不再访问这份请求。completion 负责通知，何时释放对象仍由两端代码共同安排。

调用线程继续执行后，要把 RPC 结果带回 OP-TEE，恢复暂停的安全侧处理。对于 TA 加载，后面还有校验、装载和入口调用；完成一次读文件的 RPC，并不表示原来的 OpenSession 已经成功。Linux 的 [SMC 调用循环](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/smc_abi.c)会继续处理后续返回状态，直到这次安全侧调用最终结束。

## 都叫等待，原因可能差得很远

`optee_call_queue` 的等待条目也带有 completion，这里等的是安全侧的 trusted thread 资源。固定版本既有根据协商得到的线程数量提前等待的逻辑，也有安全侧返回 `OPTEE_SMC_RETURN_ETHREAD_LIMIT` 后等待再重试的分支。[调用队列实现](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/drivers/tee/optee/call.c#L41-L185)

这里被唤醒后，调用线程可以继续争取执行资源。前面的 `req->c` 等待的则是一笔已经交给 supplicant 的 RPC 结果，两处等待处在不同阶段。

排查“TEE 调用卡住”时，我会先沿调用栈找具体等待点：是在等安全侧线程，还是在等 supplicant 回应？如果是后者，再对照请求 ID 和收发记录。函数名里的 `wait_for_completion` 说明了等待方式，调用位置才说明它在等谁。

## 现有日志能看到哪一步

前面几篇使用的 [9 月 18 日 QEMU 运行](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558)已经留下了 supplicant 的 strace。跟踪附加到了 105、151、152 这几个线程，可以看到 RECV、文件访问和 SEND 交错出现。[原始跟踪记录](https://github.com/mainkeys/mainkeys.github.io/blob/472cf654b427a8a2680e06169204e74cfbd80241/labs/optee-series/evidence/35257180558/supplicant.strace.txt)

其中有 `TEE_IOC_SUPPL_RECV ... <unfinished ...>`，后面再出现 `<... ioctl resumed>`。这是 strace 将一次尚未报告结束的系统调用拆开记录，期间穿插了其他线程的事件。至于线程具体睡在哪个 completion、锁持有了多久，这份记录没有给出答案。

这篇没有新增并发压测，也没有采集调度事件。队列、锁范围和两次通知的关系，来自上述固定源码；已有 trace 用来对照用户接口的收发。若要进一步观察实际休眠和唤醒，需要同时关联驱动等待点、Linux TID 与 `sched_switch`、`sched_wakeup` 等调度事件。

前面的图和代码摘录只展开了正常完成的路径。提交侧使用 `wait_for_completion_killable()`，等待也可能被致命信号打断；这时，另一端或许还在访问请求。信号中断、服务进程退出与正常回复各有自己的回收路径，需要另外核对，成功路径并不能说明怎样安全取消。接着往内存管理读，问题就落到了这里：请求离开队列以后，还有谁持有它，谁还可能访问它？

相关前文：[从 /dev/tee0 开始，追一次请求进入内核](/post/tee-03-linux-tee-driver.html) · [TA 还没执行完，为什么又回到了 Linux？](/post/tee-05-rpc-and-supplicant.html)

下一篇：[镜像签名没问题，为什么还要一车一授权？](/post/vehicle-authorization-nonce-avb.html) · [回到系统安全目录](/post/从前端到-SoC-Security-我准备如何构建一套系统安全知识体系.html)
