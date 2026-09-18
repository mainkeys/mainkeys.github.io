# 实验记录

本目录按运行编号保存构建配置、串口输出、系统调用跟踪和应用结果。原始 UART 保留终端控制字符与换行，文章中的摘录可在对应目录里查到。

## 35250383576：串口解析失败

- [Actions 35250383576](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35250383576)
- 实验脚本提交：`f250232e5addc557f23f1fc039f18f667743fb7e`
- 构建：2026-09-17 17:04:49～18:00:05 UTC，成功。
- QEMU：2026-09-17 18:00:05～18:02:14 UTC；记录见 [35250383576](35250383576/)。
- 19 个顶层项目 SHA 与 `sources.lock.json` 一致。来宾为 AArch64 Linux 6.18.0，OP-TEE 驱动、tee-supplicant 及示例已安装。
- 失败原因：首个环境命令返回 `__LAB_STATUS=0\r\r\n`，旧解析器只接受零个或一个 `\r`，未识别出成功状态，最终等待超时。
- 这一轮没有执行 hello_world、echo 五项检查或附加 strace；其启动日志中的 trusted_keys early TA 不能作为这些测试的证据。

修复提交 `113865db3eb885c15f5d079db6b5dd12325a4c94` 同时处理状态和文件标记，保留原始 UART；回归测试使用上述真实状态片段，并验证 LF、CRLF、CRCRLF 与 Base64 错误处理。该修复还增加 hello_world 的 42→43 检查，以及失败前尽力取回已有 guest 诊断文件的逻辑。

## 35257180558：调用与 TA 加载记录

- [Actions 35257180558](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558)，实验代码提交 `113865db3eb885c15f5d079db6b5dd12325a4c94`。
- 构建：2026-09-17 18:14:06～19:09:48 UTC；QEMU 实验：19:09:49～19:10:01 UTC。整个 job 成功结束。
- [归档目录](35257180558/)保存 18 份原始记录及传输校验表。19 个顶层源码提交与锁文件一致，配置仍为四侧 AArch64、`SPD=opteed`、TBB 关闭。
- hello_world：CA 报告 42→43，退出码 0；客户端 trace 中 `/dev/tee0` 成功打开，`TEE_IOC_INVOKE` 的 value 从 `0x2a` 返回 `0x2b`、`ret=0`；安全侧记录相同的 42→43。
- echo：正常回显、零长、短缓冲区、错误类型和 value 五项断言通过，退出码 0。两个预期错误的来源均为 `TEEC_ORIGIN_TRUSTED_APP`。
- supplicant：附加到进程 105 及其线程；两个目标 UUID 的 `.ta` 文件都有成功 `openat` 和 `read`，随后可见对应 `TEE_IOC_SUPPL_SEND`，安全侧有 REE 加载与 ELF 装载记录。
- tracer 以 SIGINT 脱离，记录 `tracer_exit=130`，附加诊断包含三条 detached；这没有结束被跟踪的 supplicant。
- TBB 认证失败仍是固定源码分析。本次正常启动和 TA 调用成功不构成 TBB、防回滚或生产平台验证。

原始启动记录保留了 FIP 头检查警告、OP-TEE insecure configuration 提示，以及 REE FS 无法获取或提交单调计数器的警告。它们没有阻止本例转向 REE TA 后端并完成调用；本轮不据此宣称可信存储或防回滚已经验证。

原始 strace 中含多线程交错、存储后端尝试及框架请求。文章只摘取能与目标 UUID 和调用对应的部分；没有采集每次 SMC 的寄存器状态或完整函数级执行轨迹。

## 文件校验与脚本版本

`transfer-checksums.json` 记录各文件的字节数与 SHA-256，用于校验 runner 文件经 Actions 日志取回后的传输一致性。实验没有另外采集 guest 文件摘要。调用结果可结合 trace、CA 断言和 UART 核对。

当前 `run-qemu.py` 还修正了文件提取命令的退出状态传播：用 `&&` 连接开始标记、Base64 和结束标记，避免 Base64 中途失败被后续 `printf` 掩盖。成功读取、部分输出后失败、缺文件三种独立 shell 回归均已通过；这里的 QEMU 原始记录仍对应上述 `113865db`。
