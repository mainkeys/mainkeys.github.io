#!/usr/bin/env python3
"""Put small, checksummed evidence in Actions logs without artifact storage."""
# SPDX-License-Identifier: BSD-2-Clause
import base64
import hashlib
import pathlib
import sys
import zlib

root = pathlib.Path(sys.argv[1])
names = ["repo-manifest.resolved.xml", "submodules.txt", "build-config.txt", "installed-examples.txt", "guest-environment.txt", "hello-world.txt", "echo-tests.txt", "hello-world.strace.txt", "supplicant.strace.txt", "supplicant-attach.txt", "supplicant-stop.txt", "results.json", "uart-normal.txt", "uart-secure.txt", "host-environment.txt", "toolchain.txt", "binary-sha256.txt", "actual-config.txt"]
for name in names:
    path = root / "evidence" / name
    if not path.is_file():
        continue
    data = path.read_bytes()
    if len(data) > 3_000_000:
        print(f"Evidence too large for log transfer: {name} ({len(data)})", file=sys.stderr)
        continue
    encoded = base64.b64encode(zlib.compress(data, 9)).decode("ascii")
    print(f"EVIDENCE_BEGIN {name} {hashlib.sha256(data).hexdigest()} {len(data)}")
    for offset in range(0, len(encoded), 2000):
        print("EVIDENCE_DATA " + encoded[offset:offset + 2000])
    print(f"EVIDENCE_END {name}")
