#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-2-Clause
# Downloads source only, into a NEW directory. Does not install tools or build.
set -euo pipefail

if [[ $# != 1 ]]; then
    printf 'Usage: bash %s NEW_LINUX_DIRECTORY\n' "$0" >&2
    exit 2
fi
for command in git repo python3 realpath findmnt; do
    command -v "$command" >/dev/null || {
        printf 'Required existing command: %s\n' "$command" >&2
        exit 1
    }
done
[[ $(uname -s) == Linux ]] || { echo 'Run inside Linux.' >&2; exit 1; }
[[ $(uname -m) == x86_64 ]] || { echo 'This guide targets an x86_64 Linux host.' >&2; exit 1; }
package_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
target=$(realpath -m -- "$1")
parent=$(dirname -- "$target")
[[ -d "$parent" && ! -e "$target" ]] || {
    echo 'Parent must exist; target must be a new directory (no overwrite).' >&2
    exit 1
}
filesystem=$(findmnt -n -o FSTYPE -T "$parent")
case "$filesystem" in
    ext4|btrfs|xfs) ;;
    *) printf 'Use the Linux filesystem (found %s), not a Windows mount.\n' "$filesystem" >&2; exit 1 ;;
esac
[[ -r "$package_dir/sources.lock.json" ]] || { echo 'Missing sources.lock.json' >&2; exit 1; }
mkdir -- "$target"
cd -- "$target"
repo init -u https://github.com/OP-TEE/manifest.git \
    -b 6d5849d5c1e4054980bf430ce1e96ebd0f532590 -m qemu_v8.xml --depth=1
python3 - "$package_dir/sources.lock.json" <<'PY'
import json
import pathlib
import sys
import xml.etree.ElementTree as ET

lock = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
manifest = ET.Element("manifest")
for project in lock["projects"]:
    # name is the upstream project name, not its checkout path.
    name = project["url"].split("github.com/", 1)[-1]
    if project["url"].startswith("https://git.trustedfirmware.org/"):
        name = project["url"].removeprefix("https://git.trustedfirmware.org/")
    ET.SubElement(manifest, "extend-project", {
        "name": name, "path": project["path"], "revision": project["commit"],
    })
output = pathlib.Path(".repo/local_manifests/series-lock.xml")
output.parent.mkdir(exist_ok=True)
ET.indent(manifest)
ET.ElementTree(manifest).write(output, encoding="utf-8", xml_declaration=True)
PY
repo sync -j4
python3 - "$package_dir/sources.lock.json" <<'PY'
import json
import pathlib
import subprocess
import sys

for project in json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["projects"]:
    head = subprocess.check_output(["git", "-C", project["path"], "rev-parse", "HEAD"], text=True).strip()
    if head != project["commit"]:
        raise SystemExit(f"HEAD mismatch: {project['path']} {head}")
print("All top-level HEADs match sources.lock.json")
PY
mkdir evidence
repo manifest -r -o evidence/repo-manifest.resolved.xml
repo forall -c 'printf "project=%s\n" "$REPO_PATH"; git submodule status --recursive' \
    > evidence/submodules.txt
python3 - "$package_dir/echo" <<'PY'
import pathlib
import shutil
import sys

destination = pathlib.Path("optee_examples/series_echo")
if destination.exists():
    raise SystemExit("Refusing to replace an existing series_echo directory")
shutil.copytree(sys.argv[1], destination)
PY
printf '\nSources prepared at %s\n' "$target"
printf 'No toolchain download, build or QEMU run has been performed. Read README.md next.\n'
