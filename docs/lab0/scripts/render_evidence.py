#!/usr/bin/env python3
"""Screenshot local pages that display recorded, unmodified command outputs."""

from html import escape
from pathlib import Path
import subprocess
import tempfile


REPORT = Path(__file__).resolve().parents[1]
ROOT = REPORT.parents[1]
EVIDENCE = REPORT / "evidence"
FIGURES = REPORT / "figures"
FIGURES.mkdir(exist_ok=True)
temporary = Path(tempfile.mkdtemp(prefix="lab0-report-screens-"))

commands = [
    "rg '^PRETTY_NAME=' /etc/os-release",
    "uname -srmo",
    "gcc --version | head -n 1",
    "aarch64-linux-gnu-gcc --version | head -n 1",
    "cmake --version | head -n 1",
    "qemu-system-aarch64 --version | head -n 1",
]
parts = []
for command in commands:
    output = subprocess.run(["bash", "-c", command], cwd=ROOT, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True).stdout.rstrip()
    parts.append(f"$ {command}\n{output}")
environment = "\n\n".join(parts) + "\n"
(EVIDENCE / "environment-summary.txt").write_text(environment, encoding="utf-8")

boot = (EVIDENCE / "qemu.log").read_text(encoding="utf-8")
bss_lines = (EVIDENCE / "bss-check.log").read_text(encoding="utf-8").splitlines()
bss = "\n".join(line for line in bss_lines if any(
    token in line for token in ["$ gdb-", "BSS start", "BSS end", "BSS bytes",
                               "Before memset:", "After memset:",
                               "BSS_CLEAR_CHECK:", "15\t", "Terminated via GDBstub"]))

cases = [
    ("environment", "01 / ENVIRONMENT", environment, 1280, 880,
     "Actual local version checks / full output: evidence/environment.txt"),
    ("boot", "02 / FOUR-CORE BOOT", boot, 1280, 900,
     "Recorded QEMU output / full output: evidence/qemu.log"),
    ("bss", "03 / BSS CLEARING CHECK", bss, 1280, 600,
     "Selected original GDB output / full output: evidence/bss-check.log"),
]

for name, title, content, width, height, note in cases:
    page = temporary / f"{name}.html"
    page.write_text("""<!doctype html><html lang="en"><meta charset="utf-8">
<style>
* { box-sizing: border-box; }
body { margin: 0; padding: 34px; background: #edf2f5; color: #e6edf3; }
.window { background: #142331; border-radius: 16px; overflow: hidden;
  box-shadow: 0 10px 28px #14233122; border: 1px solid #263d50; }
.bar { padding: 20px 28px; border-bottom: 1px solid #365064;
  background: #1e3445; font: 600 19px 'DejaVu Sans', sans-serif;
  display: flex; justify-content: space-between; color: #d4e7ec; }
.meta { color: #92b9c1; font-weight: 400; }
pre { padding: 24px 28px 18px; margin: 0; font: 24px/1.48 'DejaVu Sans Mono', monospace;
  white-space: pre-wrap; overflow-wrap: anywhere; tab-size: 4; }
.note { border-top: 1px solid #365064; padding: 16px 28px;
  font: 16px 'DejaVu Sans', sans-serif; color: #a7c4ce; }
</style><div class="window"><div class="bar"><span>""" + escape(title) +
                    "</span><span class=\"meta\">Lab 0 / 2026-10-16</span></div><pre>" +
                    escape(content.rstrip()) + "</pre><div class=\"note\">" +
                    escape(note) + "</div></div></html>", encoding="utf-8")
    args = ["google-chrome", "--headless", "--no-sandbox", "--disable-gpu",
            "--disable-background-networking", "--no-first-run", "--hide-scrollbars",
            "--force-device-scale-factor=1.5", "--virtual-time-budget=1000",
            f"--user-data-dir={temporary / ('profile-' + name)}",
            f"--window-size={width},{height}",
            f"--screenshot={FIGURES / (name + '.png')}", page.as_uri()]
    result = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=30)
    (temporary / f"{name}-chrome.log").write_text(result.stdout, encoding="utf-8")
    if result.returncode or not (FIGURES / (name + ".png")).exists():
        print(result.stdout)
        raise SystemExit(result.returncode or 1)
    print(f"Saved {FIGURES / (name + '.png')}")
