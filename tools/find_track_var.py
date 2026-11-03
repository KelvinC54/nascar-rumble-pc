"""Find the RAM bytes holding the selected locale/track on the track-select screen.

Assumes a debug build is running with PSX_DEBUG_SERVER=1 and sitting at the
title screen. Navigates to track select, then steps Right (locale) and Down
(track), snapshotting RAM, and reports bytes that follow each step exactly.
usage: python find_track_var.py [screens_to_track_select]
"""
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from psxdbg import Psx  # noqa: E402

BASE = 0x80000000
psx = Psx()


def stepping(button, steps):
    snaps = [psx.ram()]
    for _ in range(steps):
        psx.press(button, after_s=1.2)
        snaps.append(psx.ram())
    hits = []
    for off in range(0x10000, len(snaps[0])):  # skip the kernel area
        vals = [s[off] for s in snaps]
        diffs = {(b - a) & 0xFF for a, b in zip(vals, vals[1:])}
        if diffs == {1} or (diffs <= {1, (1 - len(vals)) & 0xFF} and len(set(vals)) > 2):
            hits.append((BASE + off, vals))
    return hits


def main():
    advances = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    psx.press("start", after_s=3)
    for _ in range(advances):
        psx.press("cross", after_s=2.5)
    for name, button in (("locale", "right"), ("track", "down")):
        hits = stepping(button, 4)
        print(f"{name} ({button}): {len(hits)} candidates")
        for addr, vals in hits[:20]:
            print(f"  0x{addr:08X}  {vals}")


if __name__ == "__main__":
    main()
