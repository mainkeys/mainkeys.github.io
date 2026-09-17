#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
[[ $# -ge 1 ]] || { printf 'Usage: bash %s OPTEE_ROOT [make args]\n' "$0" >&2; exit 2; }
package_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
optee_root=$(realpath -- "$1")
shift
[[ -f "$optee_root/build/qemu_v8.mk" ]] || { echo 'Missing build/qemu_v8.mk' >&2; exit 1; }
exec make -C "$optee_root/build" -f qemu_v8.mk -f "$package_dir/series.mk" \
    COMPILE_NS_USER=64 COMPILE_S_USER=64 COMPILE_S_KERNEL=64 \
    SPMC_AT_EL=n TF_A_TRUSTED_BOARD_BOOT=n RUST_ENABLE=n \
    MEASURED_BOOT_FTPM=n BR2_PACKAGE_STRACE=y CFG_TEE_CORE_LOG_LEVEL=4 "$@"
