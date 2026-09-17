#!/usr/bin/env python3
"""Recover our checksummed evidence blocks from a downloaded Actions log ZIP."""
import argparse
import base64
import hashlib
import json
import pathlib
import re
import zipfile
import zlib

parser = argparse.ArgumentParser()
parser.add_argument("archive", type=pathlib.Path)
parser.add_argument("destination", type=pathlib.Path)
args = parser.parse_args()
args.destination.mkdir(parents=True, exist_ok=True)
found = {}
with zipfile.ZipFile(args.archive) as archive:
    for item in archive.infolist():
        if item.is_dir() or item.file_size > 30_000_000:
            continue
        active = None
        chunks = []
        for line in archive.read(item).decode("utf-8-sig", errors="replace").splitlines():
            begin = re.search(r"\bEVIDENCE_BEGIN ([a-zA-Z0-9][a-zA-Z0-9_.-]*) ([0-9a-f]{64}) ([0-9]+)$", line)
            if begin:
                active = begin.groups()
                chunks = []
                continue
            data = re.search(r"\bEVIDENCE_DATA ([A-Za-z0-9+/=]+)$", line)
            if active and data:
                chunks.append(data.group(1))
                continue
            end = re.search(r"\bEVIDENCE_END ([a-zA-Z0-9][a-zA-Z0-9_.-]*)$", line)
            if active and end and end.group(1) == active[0]:
                name, digest, length = active
                if int(length) > 3_000_000:
                    raise SystemExit(f"Oversized evidence: {name}")
                raw = zlib.decompress(base64.b64decode("".join(chunks), validate=True))
                if len(raw) != int(length) or hashlib.sha256(raw).hexdigest() != digest:
                    raise SystemExit(f"Evidence checksum failed: {name}")
                path = args.destination / name
                if path.exists() and path.read_bytes() != raw:
                    raise SystemExit(f"Refusing to replace different evidence: {name}")
                path.write_bytes(raw)
                found[name] = {"sha256": digest, "bytes": len(raw)}
                active = None
if not found:
    raise SystemExit("No evidence blocks found")
(args.destination / "transfer-checksums.json").write_text(json.dumps(found, indent=2) + "\n", encoding="utf-8")
print(json.dumps(found, indent=2))
