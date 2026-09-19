---
title: 传给 TA 的参数，为什么不能只是一个指针？
date: "2026-09-09T08:00:00+08:00"
updated: "2026-09-19T08:30:00+08:00"
tags: [TEE, OP-TEE, Linux, 共享内存]
categories: [系统安全]
description: 从一个字符串回显命令出发，理解 value、memref、共享内存和 TA 的参数边界。
series: 顺着一次 TEE 调用
series_order: 4
permalink: /post/tee-04-shared-memory.html
---

前面的 hello_world 只传了一个整数，TA 加一以后再返回。换成字符串，就得处理内存了。

按平时写 C 的习惯，接口大概就是一个指针加一个长度。但 CA 的指针到了 TA 那边，还能直接用吗？

这里很容易把 CA 调 TA 想成普通函数调用。实际上，两边有各自的地址空间，中间还经过 Linux、Secure Monitor 和 TEE OS。一个地址值从 CA 传过来，并不会自动指向 TA 能访问的同一块内存。

我给前面的实验加了一个字节回显命令：CA 发送 `hello from CA`，TA 原样返回。环境仍是 OP-TEE 4.10.0、AArch64 和传统 SMC 接口；FF-A 的内存句柄流程不在这次范围内。

## 先看接口怎么写

Client API 的一个 Operation 有四个参数槽，类型写在 `paramTypes` 里。前面用的是 `value`，这次要用 `memref`。

`value` 放的是小整数，有 `a`、`b` 两个 32 位字段。它适合放命令选项、计数等简单值。`memref` 描述一段内存，要表达这段数据的位置和长度；还需要知道它是输入、输出，还是两者兼有。

libteec、内核驱动、TEE OS 和 TA 都会读取参数类型。如果 CA 发了 `VALUE_INPUT`，TA 却按 `memref.buffer` 解引用，同一个 union 在两边就成了不同的东西。所以 TA 入口得先检查类型，后面才能取值。

示例里有两个命令：`SERIES_CMD_ECHO = 0` 做字节回显，`SERIES_CMD_VALUE = 1` 让 `a` 加一、`b` 保持原值。回显命令的参数约定如下：

| 参数 | CA 侧类型 | TA 侧类型 | 用途 |
|---|---|---|---|
| 0 | `TEEC_MEMREF_TEMP_INPUT` | `TEE_PARAM_TYPE_MEMREF_INPUT` | 输入数据及字节数 |
| 1 | `TEEC_MEMREF_TEMP_OUTPUT` | `TEE_PARAM_TYPE_MEMREF_OUTPUT` | 输出缓冲区及容量 |
| 2、3 | `TEEC_NONE` | `TEE_PARAM_TYPE_NONE` | 不使用 |

命令号和参数组合由这个 TA 自己定义；Client API 提供了这些参数类型，定义在 [tee_client_api.h](https://github.com/OP-TEE/optee_client/blob/9f5e90918093c1d1cd264d8149081b64ab7ba672/libteec/include/tee_client_api.h) 中。

## 从 CA 的指针到 TA 的 buffer

![value 与 memref 在调用链中的不同传递方式](/post/tee-04-shared-memory/architecture.svg)

CA 填进 `tmpref.buffer` 的是自己的用户态虚拟地址。libteec 先处理这段内存的共享方式，再组织 ioctl 所需的参数。到了 Linux TEE 接口，内存引用可以表现为共享内存对象的标识、偏移和长度，不能简单把原来的指针整数一路透传。

驱动随后构造 OP-TEE 消息。传统 SMC 消息 ABI 里，临时内存引用与注册内存引用的描述方式也有差别。TEE OS 要根据对应对象和范围完成访问检查、映射等工作，用户 TA 最后拿到的是它自己执行环境下可使用的参数。

查这部分代码时，我会把地址和内存对象的标识分开看。字段都是整数，含义却可能已经变了；还得连着偏移和长度一起看，才能知道它实际描述哪段内存。

SMC 寄存器里传的是调用编号和约定参数，字符串本身仍留在内存里。接收方按照调用约定找到消息，再访问其中描述的共享数据。对照结构体会更清楚：[Linux TEE UAPI](https://github.com/linaro-swg/linux/blob/cf6e3218c25183cbc45551e85d0dd531f00fcc3d/include/uapi/linux/tee.h)、[OP-TEE 消息定义](https://github.com/OP-TEE/optee_os/blob/753afbbee1682f5d16fd30e87b31058a4fd4f4b8/core/include/optee_msg.h)。

## 共享内存也可能发生拷贝

这个例子用临时内存引用，CA 提供缓冲区，由库处理这次调用需要的准备和释放。写起来方便，但这条路径仍可能复制数据。

对于需要重复使用的缓冲区，Client API 还提供 `TEEC_AllocateSharedMemory()` 和 `TEEC_RegisterSharedMemory()`。前者让库分配共享内存，后者尝试把已有缓冲区注册成共享内存。注册能否直接使用原缓冲区，取决于内存条件和底层能力；libteec 必要时会使用 shadow buffer。

因此，看到 `RegisterSharedMemory` 也不能直接认定是零拷贝，还得看 libteec 实际走了哪个分支。相关说明和实现分别在 [OP-TEE 文档](https://optee.readthedocs.io/en/4.10.0/architecture/globalplatform_api.html#tee-shared-memory)和 [libteec 的预处理、后处理代码](https://github.com/OP-TEE/optee_client/blob/9f5e90918093c1d1cd264d8149081b64ab7ba672/libteec/src/tee_client_api.c)里。这次先验证参数处理，性能没有测。

## 13 个字节，要不要带上结尾的零

示例发送 `hello from CA`，一共 13 个字节。C 数组末尾有 `\0`，但协议明确不把它算进输入，也不要求 TA 额外追加它。

TA 只按收到的长度复制，不能用 `strlen()` 向后找结束符。CA 打印返回内容时也要限制长度：这段输出没有保证以零结尾，直接当 C 字符串用就可能读过头。

TA 里的主要处理如下。完整代码还检查了非零长度对应空指针的情况：

```c
if (types != TEE_PARAM_TYPES(TEE_PARAM_TYPE_MEMREF_INPUT,
                            TEE_PARAM_TYPE_MEMREF_OUTPUT,
                            TEE_PARAM_TYPE_NONE,
                            TEE_PARAM_TYPE_NONE))
    return TEE_ERROR_BAD_PARAMETERS;

size_t required = params[0].memref.size;
size_t capacity = params[1].memref.size;
params[1].memref.size = required;

if (capacity < required)
    return TEE_ERROR_SHORT_BUFFER;

if (required)
    TEE_MemMove(params[1].memref.buffer,
                params[0].memref.buffer, required);
return TEE_SUCCESS;
```

输出空间不够时，TA 填回所需长度，返回 `SHORT_BUFFER`。CA 可以据此扩大缓冲区再试。这次没有复制数据，返回的长度表示“需要多少”，不能拿它当“已经写入多少”。

框架检查了 `memref` 能不能访问，业务仍然要检查里面的内容。回显只需要关心字节数；换成解析授权或处理结构体，长度上限、字段组合、调用权限就得在 TA 里另外处理。

还有共享内存被另一侧修改的问题。安全决策依赖的数据通常需要先复制到自己控制的内存，再校验和使用；复制过程中的一致性也要由协议考虑，不能以为拷贝一次就解决了。本例只做字节回显，没有实现这类安全协议。

## 跑一下，包括故意传错的情况

CA 里放了五组断言，在同一个 Session 内依次执行。除了正常回显，还试了零长度、输出空间不足、参数类型错误，最后用 value 命令作对照。全部通过才返回零并打印 `PASS: 5 cases`：

| 场景 | 程序检查的内容 | 本次结果 |
|---|---|---|
| 正常回显 | 返回 13 字节，与输入一致；返回内容后第一个哨兵字节未被覆盖 | 通过，`0x00000000` |
| 零长度输入和输出 | 返回成功，长度为 0；使用有效指针，不混入 NULL memref 能力测试 | 通过，`0x00000000` |
| 输出容量只有 3 字节 | 返回 `SHORT_BUFFER`，报告需要 13 字节，CA 的原输出保持不变 | 通过，`0xffff0010` |
| 把参数 0 改成 value | 返回 `BAD_PARAMETERS`，不将整数解释成内存引用 | 通过，`0xffff0006` |
| value 对照 | `a` 从 41 变成 42，`b` 保持 99 | 通过，`0x00000000` |

两个错误用例还要看 `returnOrigin`。这里预期的来源是 `TRUSTED_APP`，说明 TA 已经执行到拒绝分支；如果请求先被库或驱动拦下，就没有测到这段 TA 代码。

构建环境按照系列实验包准备，把 `series_echo` 编进同一份 rootfs，然后在 QEMU 普通世界运行：

```sh
optee_series_echo
echo $?
```

下面是 [2026 年 9 月 18 日的实验记录](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558)中的实际输出，摘自 [echo-tests.txt](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/echo-tests.txt)，仅统一了串口换行：

```text
normal: result=0x00000000 origin=4
echo bytes (13): hello from CA
zero-length: result=0x00000000 origin=4
short-buffer: result=0xffff0010 origin=4
short-buffer required bytes: 13
wrong-type: result=0xffff0006 origin=4
value: result=0x00000000 origin=4
PASS: 5 cases
```

两个故意触发的错误都来自 origin 4，也就是 `TEEC_ORIGIN_TRUSTED_APP`。这说明本例确实走到了 TA 的拒绝分支。正常、零长和 value 检查则返回成功；表里的内容一致性、哨兵和字段变化由 CA 断言检查，不是每项都另打印一行。程序退出码为 0，保存在 [results.json](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/results.json)。

[安全侧 UART](https://github.com/mainkeys/mainkeys.github.io/blob/main/labs/optee-series/evidence/35257180558/uart-secure.txt) 中也能找到 UUID `4d5acb20-46c2-4bc7-9c0d-58f50a1179d2` 的 REE 加载、ELF 装载，以及 `series-echo: session opened`，可以和 CA 的结果对上。日志没有逐页记录共享内存映射，零拷贝和性能收益都不在这次验证范围内。

本例为 BSD-2-Clause 的原创教学代码，完整 [CA](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/echo/host/main.c) 和 [TA](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/echo/ta/echo_ta.c) 链接固定到实际运行提交。复现命令、组件锁定与原始记录在[实验包](https://github.com/mainkeys/mainkeys.github.io/tree/main/labs/optee-series)中。

下一篇看日志里另一件容易让人困惑的事：CA 的调用还没结束，执行却已经回到 Linux 去读文件了。

## 系列导航

1. [一次 CA 请求，到底怎么走到 TA？](/post/tee-01-ca-to-ta.html)
2. [看 TEE 代码之前，我先把 ARMv8 的异常级理清了](/post/tee-02-armv8-exception-levels.html)
3. [从 /dev/tee0 开始，追一次请求进入内核](/post/tee-03-linux-tee-driver.html)
4. 本篇：参数和共享内存
5. [TA 还没执行完，为什么又回到了 Linux？](/post/tee-05-rpc-and-supplicant.html)
6. [能调用 TA 之前，系统是怎样启动起来的？](/post/tee-06-before-the-first-call.html)

上一篇：[从 /dev/tee0 开始，追一次请求进入内核](/post/tee-03-linux-tee-driver.html)。下一篇：[TA 还没执行完，为什么又回到了 Linux？](/post/tee-05-rpc-and-supplicant.html)。
