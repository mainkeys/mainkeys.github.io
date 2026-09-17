#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-2-Clause
# Build only with a toolchain that is already installed and reviewed.
set -euo pipefail
[[ $# == 1 ]] || { printf 'Usage: bash %s OPTEE_ROOT\n' "$0" >&2; exit 2; }
package_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
optee_root=$(realpath -- "$1")
[[ -x "$optee_root/toolchains/aarch64/bin/aarch64-linux-gnu-gcc" ]] || {
    echo 'No existing upstream-layout AArch64 toolchain; see README. Nothing downloaded.' >&2
    exit 1
}
[[ -f "$optee_root/optee_examples/series_echo/ta/echo_ta.c" ]] || {
    echo 'series_echo is missing; run bootstrap first or install the example as documented.' >&2
    exit 1
}
mkdir -p "$optee_root/evidence"
bash "$package_dir/series-make.sh" "$optee_root" series-config \
    | tee "$optee_root/evidence/build-config.txt"
bash "$package_dir/series-make.sh" "$optee_root" -j"${JOBS:-2}" all \
    2>&1 | tee "$optee_root/evidence/build.log"
find "$optee_root/out-br/target" \
    -name optee_example_hello_world -o -name optee_series_echo \
    -o -name 4d5acb20-46c2-4bc7-9c0d-58f50a1179d2.ta \
    | tee "$optee_root/evidence/installed-examples.txt"
test -x "$optee_root/out-br/target/usr/bin/optee_series_echo"
test -f "$optee_root/out-br/target/lib/optee_armtz/4d5acb20-46c2-4bc7-9c0d-58f50a1179d2.ta"
