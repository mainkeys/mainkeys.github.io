#!/usr/bin/env python3
"""Read this repository's Actions status using its existing Git credential helper.

Credentials stay in memory, are never printed, and are sent only to api.github.com.
"""
import argparse
import json
import os
import pathlib
import subprocess
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = "mainkeys/mainkeys.github.io"

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(request, fp, code, msg, headers, newurl)
        if redirected is not None and urllib.parse.urlsplit(newurl).hostname != "api.github.com":
            redirected.remove_header("Authorization")
        return redirected

def credential():
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    result = subprocess.run(["git", "credential", "fill"], input=f"protocol=https\nhost=github.com\npath={REPOSITORY}.git\n\n", text=True, capture_output=True, env=env, timeout=20)
    if result.returncode:
        raise SystemExit("Existing noninteractive Git credential was unavailable.")
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    if not fields.get("password"):
        raise SystemExit("No usable GitHub credential returned.")
    return fields["password"]

parser = argparse.ArgumentParser()
parser.add_argument("--branch", default="codex/tee-series-lab")
parser.add_argument("--run", type=int)
parser.add_argument("--job", type=int, help="Download one job log instead of the run archive")
parser.add_argument("--logs", type=pathlib.Path)
args = parser.parse_args()
token = credential()
opener = urllib.request.build_opener(SafeRedirect())

def request(endpoint):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPOSITORY}/actions/{endpoint}", headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "RootPKhash-public-lab", "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with opener.open(req, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise SystemExit(f"GitHub request failed: HTTP {error.code} ({endpoint})") from None

if args.logs:
    if not (args.run or args.job):
        parser.error("--logs requires --run or --job")
    args.logs.parent.mkdir(parents=True, exist_ok=True)
    endpoint = f"jobs/{args.job}/logs" if args.job else f"runs/{args.run}/logs"
    args.logs.write_bytes(request(endpoint))
    print(json.dumps({"saved": str(args.logs), "bytes": args.logs.stat().st_size}))
elif args.run:
    data = json.loads(request(f"runs/{args.run}/jobs"))
    print(json.dumps([{k: job.get(k) for k in ("id", "name", "status", "conclusion", "steps")} for job in data["jobs"]], ensure_ascii=False))
else:
    data = json.loads(request("runs?" + urllib.parse.urlencode({"branch": args.branch, "per_page": 3})))
    print(json.dumps([{k: run.get(k) for k in ("id", "name", "status", "conclusion", "head_sha", "html_url")} for run in data["workflow_runs"]], ensure_ascii=False))
