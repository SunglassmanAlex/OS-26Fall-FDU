#!/usr/bin/env python3
"""Collect real local outputs for the Lab 0 report without changing kernel code."""

from datetime import datetime
from pathlib import Path
import hashlib
import json
import os
import pty
import re
import select
import shlex
import subprocess
import time
from zoneinfo import ZoneInfo


REPORT = Path(__file__).resolve().parents[1]
ROOT = REPORT.parents[1]
EVIDENCE = REPORT / "evidence"
EVIDENCE.mkdir(exist_ok=True)


def command_output(args):
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    return result.returncode, result.stdout


environment = []
for args in [
    ["cat", "/etc/os-release"], ["uname", "-srmo"], ["gcc", "--version"],
    ["aarch64-linux-gnu-gcc", "--version"], ["cmake", "--version"],
    ["qemu-system-aarch64", "--version"], ["git", "--version"],
]:
    code, output = command_output(args)
    if code:
        raise SystemExit(f"Environment check failed: {shlex.join(args)}\n{output}")
    environment.append(f"$ {shlex.join(args)}\n{output.rstrip()}\n")
(EVIDENCE / "environment.txt").write_text("\n".join(environment), encoding="utf-8")

build_records = []
for args in [
    ["cmake", "-S", ".", "-B", "build", "-G", "Unix Makefiles"],
    ["cmake", "--build", "build", "--target", "image"],
]:
    code, output = command_output(args)
    build_records.append(f"$ {shlex.join(args)}\n{output}")
    (EVIDENCE / "build.log").write_text("\n".join(build_records), encoding="utf-8")
    if code:
        raise SystemExit(f"Build failed; see {EVIDENCE / 'build.log'}")

# Use a real pseudo-terminal so Ctrl+A, x performs the documented QEMU exit.
args = ["cmake", "--build", "build", "--target", "qemu"]
master, slave = pty.openpty()
process = subprocess.Popen(args, cwd=ROOT, stdin=slave, stdout=slave, stderr=slave,
                           start_new_session=True)
os.close(slave)
captured = bytearray()
exit_sent = False
started = time.monotonic()
try:
    while time.monotonic() - started < 35:
        readable, _, _ = select.select([master], [], [], 0.2)
        if readable:
            try:
                chunk = os.read(master, 65536)
            except OSError:
                break
            if not chunk:
                break
            captured.extend(chunk)
        if not exit_sent and len(re.findall(rb"Hello, world! \(Core [0-3]\)", captured)) >= 4:
            os.write(master, b"\x01x")
            exit_sent = True
        if process.poll() is not None and not readable:
            break
    if process.poll() is None:
        process.terminate()
    returncode = process.wait(timeout=5)
finally:
    os.close(master)
    if process.poll() is None:
        process.kill()
        process.wait()

qemu_output = captured.decode("utf-8", errors="replace").replace("\r\n", "\n")
(EVIDENCE / "qemu.log").write_text(
    f"$ {shlex.join(args)}\n{qemu_output}", encoding="utf-8")
cores = [int(value) for value in re.findall(r"Hello, world! \(Core ([0-3])\)", qemu_output)]
passed = returncode == 0 and len(cores) == 4 and cores[0] == 0 and sorted(cores) == [0, 1, 2, 3]

layout = []
for args in [
    ["aarch64-linux-gnu-readelf", "-SW", "build/src/kernel8.elf"],
    ["aarch64-linux-gnu-readelf", "-lW", "build/src/kernel8.elf"],
    ["aarch64-linux-gnu-nm", "-n", "--defined-only", "build/src/kernel8.elf"],
]:
    code, output = command_output(args)
    if code:
        raise SystemExit(f"ELF inspection failed: {shlex.join(args)}")
    layout.append(f"$ {shlex.join(args)}\n{output}")
(EVIDENCE / "elf-layout.txt").write_text("\n".join(layout), encoding="utf-8")

_, commit = command_output(["git", "rev-parse", "HEAD"])
_, branch = command_output(["git", "branch", "--show-current"])
metadata = {
    "collected_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
    "branch": branch.strip(), "base_commit": commit.strip(),
    "main_c_sha256": hashlib.sha256((ROOT / "src/main.c").read_bytes()).hexdigest(),
    "qemu_exit_code": returncode, "core_order": cores, "boot_check_passed": passed,
    "exit_method": "Sent Ctrl+A, x through the pseudo-terminal after four Hello lines.",
}
(EVIDENCE / "validation.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(metadata, ensure_ascii=False, indent=2))
if not passed:
    raise SystemExit("QEMU boot check failed; inspect evidence/qemu.log")
