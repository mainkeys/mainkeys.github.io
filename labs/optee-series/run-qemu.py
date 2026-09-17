#!/usr/bin/env python3
"""Run the public examples in a real QEMU guest and collect unedited evidence."""
# SPDX-License-Identifier: BSD-2-Clause
import base64
import json
import pathlib
import re
import sys
import time

import pexpect

root = pathlib.Path(sys.argv[1]).resolve()
package = pathlib.Path(__file__).resolve().parent
evidence = root / "evidence"
evidence.mkdir(exist_ok=True)
secure_log = evidence / "uart-secure.txt"
if secure_log.exists():
    raise SystemExit("Refusing to overwrite a previous run's secure UART")
results = {"status": "running", "environment": "QEMU Armv8-A, traditional SMC ABI", "startedUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "checks": {}}
prompt = r"SERIES_READY# "

with (evidence / "uart-normal.txt").open("w", encoding="utf-8") as log:
    child = pexpect.spawn("bash", [str(package / "series-make.sh"), str(root), "series-console", f"SERIES_SECURE_LOG={secure_log}"], encoding="utf-8", codec_errors="replace", timeout=180)
    child.logfile_read = log

    def command(text, timeout=120):
        child.sendline(text + "; lab_status=$?; printf '\\n__LAB_STATUS=%s\\n' \"$lab_status\"")
        child.expect(r"__LAB_STATUS=([0-9]+)\r?\n", timeout=timeout)
        output, status = child.before, int(child.match.group(1))
        child.expect(prompt)
        if status:
            raise RuntimeError(f"Guest command failed ({status}): {text}\n{output}")
        return output

    def get_file(guest_path, name):
        output = command(f"printf '__FILE_BEGIN__\\n'; base64 {guest_path}; printf '\\n__FILE_END__\\n'")
        match = re.search(r"__FILE_BEGIN__\r?\n(.*?)\r?\n__FILE_END__", output, re.S)
        if not match:
            raise RuntimeError(f"Missing file markers for {guest_path}")
        data = base64.b64decode(re.sub(r"\s", "", match.group(1)), validate=True)
        (evidence / name).write_bytes(data)
        return data.decode("utf-8", errors="replace")

    try:
        child.expect(r"login:\s*")
        child.sendline("root")
        child.expect(r"# ")
        child.sendline("stty -echo")
        child.expect(r"# ")
        child.sendline("export PS1='SERIES_READY# '")
        child.expect(prompt)
        env = command("uname -a; ls -l /dev/tee*; command -v strace; command -v optee_series_echo; pidof tee-supplicant")
        (evidence / "guest-environment.txt").write_text(env, encoding="utf-8")
        command("strace -f -s 256 -e trace=openat,read,close,ioctl -o /tmp/supplicant.strace -p $(pidof tee-supplicant) 2>/tmp/supplicant-attach.txt & SERIES_TRACER=$!; sleep 1; kill -0 $SERIES_TRACER")
        hello = command("strace -s 256 -e trace=openat,close,ioctl -o /tmp/hello.strace optee_example_hello_world")
        (evidence / "hello-world.txt").write_text(hello, encoding="utf-8")
        results["checks"]["hello_world"] = {"exitCode": 0, "output": hello.strip()}
        echo = command("optee_series_echo")
        (evidence / "echo-tests.txt").write_text(echo, encoding="utf-8")
        if "PASS" not in echo:
            raise RuntimeError("Echo application did not print its asserted PASS result")
        results["checks"]["echo"] = {"exitCode": 0, "output": echo.strip()}
        command("kill -INT $SERIES_TRACER; sleep 1")
        trace = get_file("/tmp/hello.strace", "hello-world.strace.txt")
        supp = get_file("/tmp/supplicant.strace", "supplicant.strace.txt")
        get_file("/tmp/supplicant-attach.txt", "supplicant-attach.txt")
        if "ioctl(" not in trace or "/dev/tee" not in trace:
            raise RuntimeError("Expected a real TEE ioctl trace")
        if ".ta\"" not in supp or "ioctl(" not in supp:
            raise RuntimeError("Did not observe TA file loading and supplicant ioctls")
        results["checks"]["ioctl"] = "observed"
        results["checks"]["ree_ta_load"] = "TA file open plus supplicant ioctls observed; correlate with secure UART and fixed source"
        results["status"] = "passed"
        command("sync")
        child.sendcontrol("a")
        child.send("x")
        child.expect(pexpect.EOF, timeout=30)
    except Exception as error:
        results["status"] = "failed"
        results["error"] = str(error)
        raise
    finally:
        if child.isalive():
            child.sendcontrol("a")
            child.send("x")
            child.close(force=True)
        results["finishedUtc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (evidence / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(results, ensure_ascii=False, indent=2))
