"""Symbolize sampler.exe output against the exe's symbol table (llvm-nm).

usage: python sampler_report.py <exe> <samples.txt> [top]
Prints, per busy thread, the hottest functions (samples outside the exe = 'other module').
"""
import bisect
import collections
import subprocess
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nrpaths  # noqa: E402

NM = os.path.join(nrpaths.TOOLCHAIN_BIN, "llvm-nm.exe")
IMAGE_BASE = 0x140000000

exe, samples = sys.argv[1], sys.argv[2]
top = int(sys.argv[3]) if len(sys.argv) > 3 else 15
syms = []
for line in subprocess.run([NM, "-C", exe], capture_output=True, text=True).stdout.splitlines():
    parts = line.split(" ", 2)
    if len(parts) == 3 and parts[1] in "tT":
        syms.append((int(parts[0], 16), parts[2]))
syms.sort()
addrs = [a for a, _ in syms]
base = IMAGE_BASE
per_thread = collections.defaultdict(collections.Counter)
for line in open(samples):
    if line.startswith("base"):
        base = int(line.split()[1], 16)
        continue
    tid, rip = line.split()
    va = int(rip, 16) - base + IMAGE_BASE
    if va < addrs[0] or va > addrs[-1] + 0x100000:
        name = "(other module)"
    else:
        name = syms[bisect.bisect_right(addrs, va) - 1][1]
    per_thread[tid][name[:110]] += 1
busy = sorted(per_thread.items(), key=lambda kv: -sum(v for k, v in kv[1].items() if k != "(other module)"))
for tid, c in busy[:3]:
    total = sum(c.values())
    print(f"--- thread {tid}: {total} samples")
    for name, n in c.most_common(top):
        print(f"{100 * n / total:5.1f}%  {name}")
