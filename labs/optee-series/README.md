# OP-TEE QEMU 实验

这个实验配合博客中的 TEE 调用系列，用官方 `hello_world` 观察 CA 到 TA 的调用，再用独立的 [echo 示例](echo/) 检查 value、memref、参数类型和输出长度。实验还记录客户端 ioctl、tee-supplicant 读取 TA 文件的过程及两路 UART。

## 版本与配置

基于 OP-TEE **4.10.0** 的 [qemu_v8.xml](https://github.com/OP-TEE/manifest/blob/6d5849d5c1e4054980bf430ce1e96ebd0f532590/qemu_v8.xml)，manifest commit 为 `6d5849d5c1e4054980bf430ce1e96ebd0f532590`。19 个顶层项目的固定提交见 [sources.lock.json](sources.lock.json)，以下是主要组件：

| 组件 | 提交 |
| --- | --- |
| build | `53bfd321ee7fd47e450fb88c04b08ea27819f9bc` |
| optee_os | `753afbbee1682f5d16fd30e87b31058a4fd4f4b8` |
| optee_client | `9f5e90918093c1d1cd264d8149081b64ab7ba672` |
| optee_examples | `934c7edb74a26e90f68024cf441073528444177f` |
| Linux | `cf6e3218c25183cbc45551e85d0dd531f00fcc3d` |
| Trusted Firmware-A | `1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc` |

[series-make.sh](series-make.sh) 使用 QEMU `virt` Armv8 平台，普通世界与安全世界的用户态、内核态均为 AArch64。`SPMC_AT_EL=n` 对应传统 SMC 路径及 `SPD=opteed`；`TF_A_TRUSTED_BOARD_BOOT=n`，关闭 TBB。另设 `RUST_ENABLE=n`、`MEASURED_BOOT_FTPM=n`、`BR2_PACKAGE_STRACE=y`、`CFG_TEE_CORE_LOG_LEVEL=4`。

## 在 Linux 上构建

宿主机使用 x86_64 Linux，实验目录放在 ext4、btrfs 或 xfs 文件系统中，路径避免空格。需要 Bash、Git、`repo`、Python 3.9 以上、make、C/C++ 本机编译器、CMake、Ninja、rsync、cpio、bison、flex、dtc、pkg-config、util-linux，以及 [OP-TEE 构建依赖](https://optee.readthedocs.io/en/4.10.0/building/prerequisites.html)列出的开发库。运行采集脚本还需要 Python `pexpect`；Ubuntu 可安装 `python3-pexpect`。Ubuntu 22.04 的完整依赖安装命令见 [实验工作流](../../.github/workflows/optee-lab.yml)。

在本仓库根目录执行，`optee_root` 必须是尚不存在的目录：

```bash
lab_package="$(realpath labs/optee-series)"
optee_root="$HOME/tee-labs/optee-4.10.0"
mkdir -p "$(dirname "$optee_root")"
bash "$lab_package/bootstrap-linux.sh" "$optee_root"

# 查看工具链下载目标，再下载和解压 AArch64 工具链。
bash "$lab_package/series-make.sh" "$optee_root" -n aarch64-toolchain
bash "$lab_package/series-make.sh" "$optee_root" aarch64-toolchain
JOBS=2 bash "$lab_package/build-linux.sh" "$optee_root"
```

bootstrap 会同步并校验固定提交，导出 manifest 与 submodule 状态，再把本例复制到 `optee_examples/series_echo/`。失败时会保留目录。工具链为 Arm GNU Toolchain 14.3.Rel1；上游下载目标不校验归档摘要，来源核验需对照 Arm 发布的校验信息。这里只需 `aarch64-toolchain`，通用 `toolchains` 目标还会安装 Rust 工具链。

构建日志与配置保存在 `$optee_root/evidence/`。官方 Buildroot 示例包规则会构建并安装 `optee_example_hello_world`、`optee_series_echo` 和本例 TA；不需要手动改 rootfs。修改示例后，先同步到实验目录中的 `optee_examples/series_echo/`，再运行构建。

## 运行并收集结果

以下命令启动 QEMU，运行原版 hello_world 和 echo 检查，并将结果、客户端与 supplicant trace、两路 UART 保存到 `$optee_root/evidence/`：

```bash
python3 "$lab_package/run-qemu.py" "$optee_root"
```

脚本会拒绝覆盖已有的 `evidence/uart-secure.txt`。重复实验前先另行保存旧记录。RPC 判断需要交叉查看目标 UUID 的成功文件读取、`TEE_IOC_SUPPL_RECV/SEND`、安全侧 ELF 装载及 CA 结果，不能只靠脚本的字符串检查。

也可以手动操作来宾。下面在宿主机启动 QEMU，并分别记录普通世界和安全世界串口：

```bash
run_dir=$(mktemp -d "$optee_root/evidence/run.XXXXXX")
export lab_package optee_root run_dir
script -q -e -f -c \
  'bash "$lab_package/series-make.sh" "$optee_root" series-console SERIES_SECURE_LOG="$run_dir/uart-secure.log"' \
  "$run_dir/uart-normal.log"
```

QEMU 会直接启动；以 `root` 登录来宾。先附加到 init 脚本启动的 supplicant，再运行应用：

```sh
strace -f -s 256 -e trace=openat,read,close,ioctl \
  -o /tmp/supplicant.strace -p $(pidof tee-supplicant) \
  2>/tmp/supplicant-attach.txt &
tracer_pid=$!
sleep 1
kill -0 "$tracer_pid"
strace -s 256 -e trace=openat,close,ioctl \
  -o /tmp/hello.strace optee_example_hello_world
echo "hello_world_exit=$?"
optee_series_echo
echo "echo_exit=$?"
kill -INT "$tracer_pid"
wait "$tracer_pid"; tracer_status=$?
printf 'tracer_exit=%s (0 or 130 expected)\n' "$tracer_status"
cat /tmp/hello.strace /tmp/supplicant.strace /tmp/supplicant-attach.txt
```

上述命令在来宾中执行。trace 位于临时 rootfs，退出前应另行保存；终端输出已写入宿主机的 `uart-normal.log`。用 `Ctrl-a x` 退出 QEMU，`Ctrl-a c` 可切换 monitor。

## 示例接口与已记录的结果

echo 的 UUID 是 `4d5acb20-46c2-4bc7-9c0d-58f50a1179d2`，属于 `TA_FLAGS=0` 的用户 TA，使用开发密钥签名。`SERIES_CMD_ECHO=0` 接收 `MEMREF_INPUT, MEMREF_OUTPUT, NONE, NONE`，按字节长度回显，不追加 NUL；输出不足时更新所需长度，返回 `SHORT_BUFFER`，不部分复制。`SERIES_CMD_VALUE=1` 接收 `VALUE_INOUT, NONE, NONE, NONE`，令 `a` 按 uint32_t 加一，保留 `b`。

[已完成的实验](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558)运行于 x86_64 Ubuntu 22.04 GitHub Actions 宿主机，QEMU 测试时间为 **2026-09-17 19:09:49～19:10:01 UTC（北京时间 9 月 18 日）**。实际运行脚本对应提交 [113865db](https://github.com/mainkeys/mainkeys.github.io/blob/113865db3eb885c15f5d079db6b5dd12325a4c94/labs/optee-series/run-qemu.py)，结果如下：

| 检查 | 结果 |
| --- | --- |
| 官方 hello_world | 42 → 43，退出码 0；[客户端 ioctl](evidence/35257180558/hello-world.strace.txt)与安全侧日志相符 |
| 正常回显、零长度、value | CA 断言通过；正常输入为 13 字节，不含末尾 NUL |
| 短缓冲区、错误参数类型 | 分别返回 `0xffff0010`、`0xffff0006`，origin 均为 4；短缓冲区报告需要 13 字节 |
| REE TA 加载 | 两个目标 UUID 均有成功 open/read、supplicant 响应和安全侧 ELF 装载记录 |

[echo 完整输出](evidence/35257180558/echo-tests.txt)为 `PASS: 5 cases`，程序退出码为 0。两个预期错误的 origin 断言为 `TEEC_ORIGIN_TRUSTED_APP`；成功结果不依赖 origin 判定。原始记录、配置和摘要见 [evidence/35257180558](evidence/35257180558/)，其他运行记录见 [实验记录](evidence/README.md)。

当前采集脚本相对 `113865db` 增加了文件提取时的 `&&` 失败传播修复，该差异仅经过 shell 回归，未重新执行完整 QEMU 实验。

本实验未验证 TBB 镜像认证、防回滚、可信存储安全性、零拷贝性能或真实 SoC 隔离。启动日志中的 FIP 头检查、insecure configuration 和 REE FS 单调计数器警告均保留。19 个顶层提交与导出的 manifest 一致；文件摘要用于核对归档传输字节，不是从 guest 开始的端到端摘要认证，也不替代源码或编译器来源核验。

## 许可证

本目录示例与脚本采用 [BSD-2-Clause](LICENSE)。官方 hello_world 和其他上游组件沿用各自的许可证；本目录不包含其源码树、工具链或二进制产物。
