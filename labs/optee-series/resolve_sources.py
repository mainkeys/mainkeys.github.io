#!/usr/bin/env python3
"""Resolve the release's top-level Git refs; this does NOT run repo sync."""
import concurrent.futures
import datetime
import json
import pathlib
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

RELEASE = "4.10.0"
MANIFEST_COMMIT = "6d5849d5c1e4054980bf430ce1e96ebd0f532590"
BASE = f"https://raw.githubusercontent.com/OP-TEE/manifest/{MANIFEST_COMMIT}/"
ROOT = pathlib.Path(__file__).resolve().parent


def read_xml(name):
    with urllib.request.urlopen(BASE + name, timeout=60) as response:
        return ET.fromstring(response.read())


def resolve(project):
    ref = project["revision"]
    if len(ref) == 40 and all(c in "0123456789abcdef" for c in ref):
        project["commit"] = ref
        project["resolution"] = "commit pinned in upstream manifest"
        return project
    # The Linux repository's complete ref advertisement is very large. Use
    # GitHub's exact-ref API rather than fetching that advertisement.
    if project["path"] == "linux":
        endpoint = "https://api.github.com/repos/linaro-swg/linux/git/ref/" + ref.removeprefix("refs/")
        with urllib.request.urlopen(endpoint, timeout=60) as response:
            obj = json.load(response)["object"]
        project["refObject"] = obj["sha"]
        while obj["type"] == "tag":
            with urllib.request.urlopen(obj["url"], timeout=60) as response:
                obj = json.load(response)["object"]
        if obj["type"] != "commit":
            raise RuntimeError("Linux ref does not identify a commit")
        project["commit"] = obj["sha"]
        project["resolution"] = "GitHub Git exact-ref API, annotated tag peeled"
        return project
    result = None
    for attempt in range(3):
        try:
            result = subprocess.run(
                ["git", "ls-remote", project["url"], ref, ref + "^{}"],
                capture_output=True, text=True, check=True, timeout=90,
            )
            break
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print(f"Retry {attempt + 1}: {project['path']}", flush=True)
    if result is None:
        raise RuntimeError(f"Could not resolve {project['url']} {ref}")
    refs = dict(line.split()[::-1] for line in result.stdout.splitlines())
    if ref not in refs:
        raise RuntimeError(f"Missing ref: {project['url']} {ref}")
    project["commit"] = refs.get(ref + "^{}", refs[ref])
    project["refObject"] = refs[ref]
    project["resolution"] = "git ls-remote (peeled when annotated)"
    print(f"Resolved {project['path']}: {project['commit']}", flush=True)
    return project


def main():
    docs = [read_xml("common.xml"), read_xml("qemu_v8.xml")]
    remotes = {r.attrib["name"]: r.attrib["fetch"] for d in docs for r in d.findall("remote")}
    projects = []
    for doc in docs:
        for p in doc.findall("project"):
            projects.append({
                "path": p.attrib["path"],
                "url": remotes[p.attrib.get("remote", "github")] + "/" + p.attrib["name"],
                "revision": p.attrib["revision"],
                "syncSubmodules": p.attrib.get("sync-s") == "true",
            })
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        resolved = list(pool.map(resolve, projects))
    lock = {
        "schemaVersion": 1,
        "release": RELEASE,
        "manifest": {
            "url": "https://github.com/OP-TEE/manifest.git",
            "file": "qemu_v8.xml",
            "includedFiles": ["common.xml"],
            "tag": RELEASE,
            "tagObject": "5dc349cf004db361afc70e76af1a947c88ea7cf8",
            "commit": MANIFEST_COMMIT,
        },
        "resolvedAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Upstream manifest top-level project refs only; not a repo manifest -r export. No repo sync, submodule resolution, download verification, compilation or QEMU execution is claimed.",
        "projects": sorted(resolved, key=lambda p: p["path"]),
    }
    (ROOT / "sources.lock.json").write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Resolved {len(resolved)} top-level project refs")


if __name__ == "__main__":
    main()
