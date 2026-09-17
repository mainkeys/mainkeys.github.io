#!/usr/bin/env python3
"""Run the public examples in a real QEMU guest and collect unedited evidence."""
# SPDX-License-Identifier: BSD-2-Clause
import json
import pathlib
import re
import sys
import time

import pexpect
from console_protocol import STATUS_PATTERN, decode_guest_file

root = pathlib.Path(sys.argv[1]).resolve()
package = pathlib.Path(__file__).resolve().parent
evidence = root / "evidence"
evidence.mkdir(exist_ok=True)
secure_log = evidence / "uart-secure.txt"
if secure_log.exists():
    raise SystemExit("Refusing to overwrite a previous run's secure UART")
results = {"status": "running", "environment": "QEMU Armv8-A, traditional SMC ABI", "startedUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "checks": {}}
prompt = r"SERIES_READY# "
guest_ready = False
tracer_started = False

with (evidence / "uart-normal.txt").open("w", encoding="utf-8") as log:
    child = pexpect.spawn("bash", [str(package / "series-make.sh"), str(root), "series-console", f"SERIES_SECURE_LOG={secure_log}"], encoding="utf-8", codec_errors="replace", timeout=180)
    child.logfile_read = log

    def command(text, timeout=120):
        child.sendline(text + "; lab_status=$?; printf '\\n__LAB_STATUS=%s\\n' \"$lab_status\"")
        child.expect(STATUS_PATTERN, timeout=timeout)
        output, status = child.before, int(child.match.group(1))
        child.expect(prompt)
        if status:
            raise RuntimeError(f"Guest command failed ({status}): {text}\n{output}")
        return output

    def get_file(guest_path, name, timeout=120):
        output = command(f"test -f {guest_path} && {{ printf '__FILE_BEGIN__\\n' && base64 {guest_path} && printf '\\n__FILE_END__\\n'; }}", timeout=timeout)
        data = decode_guest_file(output)
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
        guest_ready = True
        env = command("uname -a; ls -l /dev/tee*; command -v strace; command -v optee_series_echo; pidof tee-supplicant")
        (evidence / "guest-environment.txt").write_text(env, encoding="utf-8")
        command("strace -f -s 256 -e trace=openat,read,close,ioctl -o /tmp/supplicant.strace -p $(pidof tee-supplicant) 2>/tmp/supplicant-attach.txt & SERIES_TRACER=$!; sleep 1; kill -0 $SERIES_TRACER")
        tracer_started = True
        hello = command("strace -s 256 -e trace=openat,close,ioctl -o /tmp/hello.strace optee_example_hello_world")
        (evidence / "hello-world.txt").write_text(hello, encoding="utf-8")
        if "Invoking TA to increment 42" not in hello or "TA incremented value to 43" not in hello:
            raise RuntimeError("hello_world did not report the expected 42 to 43 result")
        results["checks"]["hello_world"] = {"exitCode": 0, "output": hello.strip()}
        echo = command("optee_series_echo")
        (evidence / "echo-tests.txt").write_text(echo, encoding="utf-8")
        if "PASS: 5 cases" not in echo:
            raise RuntimeError("Echo application did not print its asserted PASS result")
        results["checks"]["echo"] = {"exitCode": 0, "output": echo.strip()}
        stopped = command('kill -INT "$SERIES_TRACER" && { for attempt in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$SERIES_TRACER" 2>/dev/null || break; sleep 0.2; done; ! kill -0 "$SERIES_TRACER" 2>/dev/null; } && { wait "$SERIES_TRACER"; tracer_status=$?; printf "tracer_exit=%s\\n" "$tracer_status"; test "$tracer_status" -eq 0 -o "$tracer_status" -eq 130; }', timeout=15)
        tracer_started = False
        (evidence / "supplicant-stop.txt").write_text(stopped, encoding="utf-8")
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
        # Preserve whatever exists before the ephemeral guest is shut down.
        # Recovery failures must not replace the original test failure.
        if guest_ready and child.isalive():
            failures = []
            try:
                child.sendcontrol("c")
                child.sendline("")
                child.expect(prompt, timeout=5)
                if tracer_started:
                    command('kill -INT "$SERIES_TRACER" 2>/dev/null || true', timeout=5)
                for guest_path, name in (
                    ("/tmp/supplicant-attach.txt", "supplicant-attach.txt"),
                    ("/tmp/hello.strace", "hello-world.strace.txt"),
                    ("/tmp/supplicant.strace", "supplicant.strace.txt"),
                ):
                    try:
                        get_file(guest_path, name, timeout=10)
                    except Exception as capture_error:
                        failures.append(f"{name}: {capture_error}")
            except Exception as recovery_error:
                failures.append(str(recovery_error))
            results["diagnosticCaptureErrors"] = failures
        raise
    finally:
        try:
            if child.isalive():
                child.sendcontrol("a")
                child.send("x")
                try:
                    child.expect(pexpect.EOF, timeout=5)
                finally:
                    child.close(force=True)
        except Exception as cleanup_error:
            results["cleanupError"] = str(cleanup_error)
        results["finishedUtc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (evidence / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(results, ensure_ascii=False, indent=2))
