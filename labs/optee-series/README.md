# TEE 系列公开实验包

这个目录保存博客第一季的最小实验材料。`echo/` 是独立的 CA/TA 示例，不修改官方 `hello_world`。本目录不包含上游源码、工具链、磁盘镜像或生成的 TA。

**当前验证状态：** 首次 Actions 已完成源码核对和完整编译，QEMU 启动到了来宾 shell，TEE 驱动、supplicant 和两个示例均已安装。自动化在首个环境命令后因串口 CRCRLF 换行解析超时，尚未执行 hello_world 与五项检查。当前已修复状态/文件标记解析，并用首跑原始状态片段做回归验证，等待重跑。`sources.lock.json` 锁定的 19 个顶层提交均与首跑导出的 `repo-manifest.resolved.xml` 一致。

## 本次无人值守运行

本次使用公开仓库的标准 `ubuntu-22.04` GitHub Actions runner，Linux 工作区为 `/home/runner/optee-series`。它是实验的宿主机；QEMU 模拟的是 Armv8-A 来宾，不依赖本机 Windows 的 WSL 是否可启动。

工作流见 [optee-lab.yml](../../.github/workflows/optee-lab.yml)，只自动响应独立 `codex/tee-series-lab` 分支的实验文件变更。它不会发布博客，也没有定时执行设置。发布仍由 main 分支原有 Pages 工作流负责。

`run-qemu.py` 自动登录新启动的来宾，先附加 strace 到现有 tee-supplicant，再运行官方 hello_world 和本系列五项检查，取回 CA、supplicant 与两侧 UART。每一步失败会使任务失败，不以进程启动成功代替实验成功。

为避免额外 artifact/cache 存储，本次把必要文本记录压缩、带 SHA-256 摘要写入 Actions job 日志，由 `tools/blog/collect-lab-evidence.py` 解码并验证。该摘要校验用于确认取回的字节未变，不代替上游源码或编译器的来源认证。

本次执行入口：[首次实验运行](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35250383576)。以下仍保留普通 Linux 机器上的手动复现方法，和自动化脚本使用相同源码与编译选项。

## 固定版本与配置

以 OP-TEE **4.10.0** 的 `qemu_v8.xml` 为基线。manifest tag object 是 `5dc349cf004db361afc70e76af1a947c88ea7cf8`，对应 commit 是 `6d5849d5c1e4054980bf430ce1e96ebd0f532590`。完整列表见 [sources.lock.json](sources.lock.json)。常用阅读入口：

| 组件 | 本系列源码提交 |
| --- | --- |
| build | `53bfd321ee7fd47e450fb88c04b08ea27819f9bc` |
| optee_os | `753afbbee1682f5d16fd30e87b31058a4fd4f4b8` |
| optee_client | `9f5e90918093c1d1cd264d8149081b64ab7ba672` |
| optee_examples | `934c7edb74a26e90f68024cf441073528444177f` |
| Linux | `cf6e3218c25183cbc45551e85d0dd531f00fcc3d` |
| Trusted Firmware-A | `1d5aa939bc8d3d892e2ed9945fa50e36a1a924cc` |

`series-make.sh` 将条件编译选项作为 make 命令行变量传入，避免在上游已解析条件分支以后再覆盖变量：

- `COMPILE_NS_USER=64`、`COMPILE_S_USER=64`、`COMPILE_S_KERNEL=64`；上游 `COMPILE_NS_KERNEL` 固定为 64。
- `SPMC_AT_EL=n`，因此 TF-A 使用 `SPD=opteed`，讨论传统 SMC 调用路径。
- `TF_A_TRUSTED_BOARD_BOOT=n`。运行成功只能说明这一配置能够启动，不能用来证明镜像认证、吊销或防回滚工作正常。
- `RUST_ENABLE=n`、`MEASURED_BOOT_FTPM=n`，关闭这次实验不需要的 Rust 示例与 fTPM；这两项并非 4.10.0 的原始默认值。
- `BR2_PACKAGE_STRACE=y`、`CFG_TEE_CORE_LOG_LEVEL=4`，保留 CA 系统调用与安全世界调试线索。

这套配置运行于 QEMU 的 `virt` Armv8 平台；宿主机是 x86_64 Linux，四侧执行代码均为 AArch64。它不能代替任何实际 SoC 的启动链、外设隔离或产线配置验证。

## 准备源码与工具

先按 [OP-TEE prerequisites](https://optee.readthedocs.io/en/4.10.0/building/prerequisites.html) 为 Linux 安装构建依赖，准备可用的 `repo`、Git、Python 3、make、C/C++ 本机编译器、CMake、Ninja、rsync、cpio、bison、flex、dtc、pkg-config，以及该页面列出的开发库。包安装属于宿主机准备工作，脚本不调用 `sudo`、更改系统组件或自行重启。

在 WSL 中把整个实验工作区放进发行版自己的 Linux 文件系统，例如 `$HOME/tee-labs`；不要在 `/mnt/c`、`/mnt/f` 上构建。先人工建立父目录，再指定一个**尚不存在**的实验目录：

```bash
# lab_package 指向本仓库中的 labs/optee-series；它可以位于 Windows 挂载盘。
lab_package=/mnt/f/code/mainkeys.github.io/labs/optee-series
mkdir -p "$HOME/tee-labs"
bash "$lab_package/bootstrap-linux.sh" "$HOME/tee-labs/optee-4.10.0"
optee_root="$HOME/tee-labs/optee-4.10.0"
```

bootstrap 只在这个新目录中执行：固定 manifest 初始化、生成锁定顶层 SHA 的 local manifest、`repo sync`、校验每个 `HEAD`、导出 `repo manifest -r` 与递归 submodule 状态，再复制 `echo/` 为 `optee_examples/series_echo/`。失败时保留现场，不删除原有工作区；不要以相同路径重复初始化来掩盖失败。

仓库中的 `resolve_sources.py` 只在需要重新核对 release 引用时手动运行。Linux 仓库使用 GitHub exact-ref API 解析大仓库 tag，其余 tag 用 `git ls-remote`，原来就是 commit 的引用保留上游值。一次解析不能证明 tag 签名可信、源码编译成功或所有依赖均已下载。

准备 AArch64 工具链时，先阅读已固定的 `build/toolchain.mk`。这次只需要其中的 `aarch64-toolchain` 目标：

```bash
# 第一步只显示将执行的下载、解压与链接操作。
bash "$lab_package/series-make.sh" "$optee_root" -n aarch64-toolchain
# 审阅后单独下载和解压；这一步不构建系统。
bash "$lab_package/series-make.sh" "$optee_root" aarch64-toolchain
```

该固定版本的 x86_64 目标使用 Arm GNU Toolchain 14.3.rel1。下载器本身不做摘要校验；使用前应与 Arm 发布页提供的校验信息核对归档，并记录实际 `sha256sum`。不要用通用 `make toolchains` 替代这里的目标：固定版本还会执行 Rust 工具链安装流程。构建脚本要求 `toolchains/aarch64/bin/aarch64-linux-gnu-gcc` 已存在，不会为了绕过缺失检查而临时下载并执行工具。

## 构建与 Buildroot 接入

```bash
JOBS=2 bash "$lab_package/build-linux.sh" "$optee_root"
```

选择 `JOBS=2` 是保守的内存默认值，可以根据宿主机容量提高。脚本记录 make 配置、完整构建日志与安装位置，保存在 Linux 实验目录的 `evidence/` 中。

接入方式依据固定的官方构建规则：`optee_examples/CMakeLists.txt` 会扫描带有 `CMakeLists.txt` 的直接子目录；`build/br-ext/package/optee_examples_ext/optee_examples_ext.mk` 以 CMake 构建 CA，并遍历 `*/ta/Makefile` 构建 TA。TA 通过上游 SDK 的 make 规则生成，并由同一包的安装钩子放入 `/lib/optee_armtz`。因此新增 `series_echo` 目录即可接入，无须手工更改 Buildroot 生成的 `.config`，也不需要向 rootfs 临时塞文件。

构建后检查下列文件；CA 是 AArch64 可执行文件，TA 是由开发密钥签名的教学产物：

```text
out-br/target/usr/bin/optee_example_hello_world
out-br/target/usr/bin/optee_series_echo
out-br/target/lib/optee_armtz/4d5acb20-46c2-4bc7-9c0d-58f50a1179d2.ta
```

更改本目录的示例后，需要把修改同步到 Linux 的 `optee_examples/series_echo/`，再运行构建。上游 `buildroot` 目标会刷新 OP-TEE 包的 stamp；这里不提供清空既有目录的重置命令。首次构建可能还会下载 Buildroot 包与 QEMU 构建依赖，应保留失败日志并解决具体错误。

## 回显示例的接口与检查

UUID 为 `4d5acb20-46c2-4bc7-9c0d-58f50a1179d2`。`TA_FLAGS=0`，普通用户 TA，不是伪 TA。共享定义在 `echo/ta/include/series_echo_ta.h`。

| 命令 | TA 接收的四个参数类型 | 行为 |
| --- | --- | --- |
| `SERIES_CMD_ECHO=0` | `MEMREF_INPUT, MEMREF_OUTPUT, NONE, NONE` | 回显指定数量的原始字节；长度不包含额外 NUL。 |
| `SERIES_CMD_VALUE=1` | `VALUE_INOUT, NONE, NONE, NONE` | `a` 加 1，按 uint32_t 回绕；保留 `b`。 |

CA 使用 temporary memref，TA 看见的是普通 input/output memref。TA 先检查整个 `paramTypes` 再访问 union。短缓冲区时先把输出 `size` 更新为所需字节数，再返回 `TEE_ERROR_SHORT_BUFFER`；不进行部分拷贝。零长输入返回成功、输出长度 0，不读取或写入缓冲区。只有长度非零才调用 `TEE_MemMove`，因此不对空指针执行零长拷贝。

CA 的五项检查为：正常输入字节完全一致且不写额外 NUL、零长输入、短缓冲区返回所需长度且保持原输出、错误类型被 TA 拒绝、value 的两个字段按合同变化。只有全部通过才打印 `PASS: 5 cases` 并以 0 退出。这里写的是程序判定条件，尚不是运行日志。

`returnOrigin` 每次调用都会记录。仅对两个有意触发的 TA 错误断言 `TEEC_ORIGIN_TRUSTED_APP`，确认错误确实到达 TA；成功调用不靠 origin 判定。这不意味着 libteec、Linux 或 OP-TEE core 返回的其他错误也应该是同一 origin。也不能只看 ioctl 的 Linux 返回值，就当作 TA 命令执行成功。

## 两路 UART 与系统调用证据

上游 `make run-only` 使用两个 `soc_term.py` TCP 终端：普通世界默认端口 54320，安全世界默认 54321。它带 `-S`，要在 QEMU monitor 输入 `c` 才继续。

本包的 `series-console` 使用同一组上游 `QEMU_BASE_ARGS`，将普通世界接到当前终端、安全世界写入单独文件，不暴露宿主机共享目录。为避免覆盖旧证据，每次建立新的运行目录：

```bash
run_dir=$(mktemp -d "$optee_root/evidence/run.XXXXXX")
export lab_package optee_root run_dir
script -q -e -f -c \
  'bash "$lab_package/series-make.sh" "$optee_root" series-console SERIES_SECURE_LOG="$run_dir/uart-secure.log"' \
  "$run_dir/uart-normal.log"
```

这个 helper 不传 `-S`，所以会直接开始启动。QEMU 的 `mon:stdio` 可用 `Ctrl-a c` 切换 monitor、`Ctrl-a x` 退出。正常关机或退出后保留两个文件。`script` 记录中可能含有终端控制字符；原始记录应保留，文章只摘取能够对应同一次运行的行。

在虚拟机普通世界以 root 登录后执行：

```sh
uname -a
ls -l /dev/tee0 /dev/teepriv0
optee_example_hello_world
echo "hello_world_exit=$?"
strace -f -yy -s 160 -e trace=openat,ioctl,mmap,munmap,close \
    -o /tmp/series-ca.strace optee_series_echo
echo "echo_exit=$?"
cat /tmp/series-ca.strace
```

`hello_world` 应先单独跑原版；本系列的 echo 示例不能替代原版验证。`strace` 中 ioctl 的显示名称取决于 guest strace 的解码版本，要对照固定 Linux `include/uapi/linux/tee.h` 中的定义。临时共享内存是否走注册、分配或 shadow buffer 由这套实现和实际能力协商决定，应从真实记录核对，不能把每次调用固定写成同一组 ioctl。

## 观察用户 TA 加载 RPC

先启动干净的 QEMU 实例，避免把之前已经加载的 TA 当作首次加载。初始 `tee-supplicant` 由 `/etc/init.d/S30optee` 启动；在**实验虚拟机里**停掉它，再以前台方式由 strace 启动，收集加载文件请求：

```sh
/etc/init.d/S30optee stop
strace -f -yy -s 160 -e trace=openat,read,close,ioctl \
    -o /tmp/series-supplicant.strace /usr/sbin/tee-supplicant /dev/teepriv0 \
    >/tmp/series-supplicant.log 2>&1 &
tracer_pid=$!
optee_series_echo
echo "rpc_case_exit=$?"
cat /tmp/series-supplicant.strace
cat /tmp/series-supplicant.log
```

从 supplicant trace 找到本示例 UUID 对应 `.ta` 的实际路径，再同安全 UART 的加载日志、CA OpenSession 结果交叉检查。即便观察到文件读取，也要沿固定源码的 RPC 命令分发解释其用途，不凭一次 `read()` 声称完成了完整调用链追踪。默认示例是用户 TA；内建 early TA、pseudo TA 或已经驻留的实例不一定触发同样的文件读取。

结束此次实验直接退出并重新启动 QEMU，可恢复原 init 脚本启动方式。不要把这段 guest 管理命令搬到宿主机执行。若 trace 没有看到加载事件，应记录当前 TA 生命周期和失败点，不补写预想日志。

第六篇的 TF-A 认证失败路径以固定源码核对；当前 `TF_A_TRUSTED_BOARD_BOOT=n`，没有镜像篡改认证实验。将来切换 TBB 开关要遵循上游要求先清理 `arm-tf`，并另建实验记录，不能混用这次启动日志。

## 证据与来源

一次可发布的实验至少保留：实际宿主环境、工具链版本与摘要、`repo-manifest.resolved.xml`、submodule 状态、make 配置、构建成功记录、两路 UART、官方 hello_world 的退出码、echo 五项结果及退出码、CA strace、supplicant trace。只对外发布必要且核对过的文本记录；私有路径、凭据和主机信息先人工检查。

- [固定 manifest](https://github.com/OP-TEE/manifest/blob/6d5849d5c1e4054980bf430ce1e96ebd0f532590/qemu_v8.xml)
- [固定 qemu_v8.mk](https://github.com/OP-TEE/build/blob/53bfd321ee7fd47e450fb88c04b08ea27819f9bc/qemu_v8.mk)
- [固定 common.mk](https://github.com/OP-TEE/build/blob/53bfd321ee7fd47e450fb88c04b08ea27819f9bc/common.mk)
- [固定 Buildroot 示例包规则](https://github.com/OP-TEE/build/blob/53bfd321ee7fd47e450fb88c04b08ea27819f9bc/br-ext/package/optee_examples_ext/optee_examples_ext.mk)
- [固定官方 hello_world](https://github.com/linaro-swg/optee_examples/tree/934c7edb74a26e90f68024cf441073528444177f/hello_world)
- [固定 libteec 临时 memref 处理](https://github.com/OP-TEE/optee_client/blob/9f5e90918093c1d1cd264d8149081b64ab7ba672/libteec/src/tee_client_api.c)
- [QEMU 官方说明](https://optee.readthedocs.io/en/4.10.0/building/devices/qemu.html#qemu-v8)

本包示例与脚本采用 BSD-2-Clause，见 [LICENSE](LICENSE)。接口布局依据上述公开 API 与构建规则编写。上游 checkout 保留其自身许可、作者信息和签名材料；本包许可不覆盖上游项目。
