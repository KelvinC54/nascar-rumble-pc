"""Grab hi-res presented frames from a demo race on the debug build (headless).

usage: python shot_probe.py <label> [--pack <dir>|none] [--res 4x] [--at 40,70,100 | --frames 6200,7400] [--loc N]
Writes <workspace>/shots/<label>-<t>.png (or <label>-f<frame>.png with --frames)
"""
import argparse
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psxdbg import Psx  # noqa: E402
import capture_all  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("label")
ap.add_argument("--pack", default=capture_all.PACK)
ap.add_argument("--res", default="4x")
ap.add_argument("--at", default="40,70,100")
ap.add_argument("--frames", default="", help="guest frame numbers instead of seconds")
ap.add_argument("--loc", type=int, default=0)
ap.add_argument("--trk", type=int, default=1)
a = ap.parse_args()
out = os.path.join(capture_all.ROOT, "shots")
os.makedirs(out, exist_ok=True)
on = a.pack != "none"
pack = capture_all.PACK if not on else a.pack
state = capture_all.STATE.format(loc=a.loc, trk=a.trk, pack=pack.replace("\\", "/"))
state = state.replace("replacements = false\ndump = true",
                      f"replacements = {'true' if on else 'false'}\ndump = false")
with open(os.path.join(capture_all.DEBUG, "mods", "state.toml"), "w", newline="\n") as f:
    f.write(state)
env = dict(os.environ, PSX_DEBUG_SERVER="1", PSX_INTERNAL_RESOLUTION=a.res, PSX_HOST_MUTE="1")
log = open(os.path.join(capture_all.DEBUG, "shot_probe.log"), "w")
proc = subprocess.Popen([os.path.join(capture_all.DEBUG, "NascarRumble_Recompiled.exe"), "--no-launcher",
                         "--headless-opengl", "--game", "game.toml", "--disc", capture_all.DISC,
                         "--debug-port", "4370"], cwd=capture_all.DEBUG, env=env, stdout=log, stderr=subprocess.STDOUT)
psx = Psx()
start = time.time()
for f in [int(x) for x in a.frames.split(",") if x]:
    while True:
        try:
            cur = psx.cmd("frame").get("frame", 0)
        except OSError:
            cur = 0
        if cur >= f:
            break
        time.sleep(0.02 if f - cur < 30 else 0.3)
    path = os.path.join(out, f"{a.label}-f{f}.png").replace("\\", "/")
    print(f, cur, psx.cmd("screenshot_hires", path=path), flush=True)
for t in [] if a.frames else [int(x) for x in a.at.split(",")]:
    time.sleep(max(0, start + t - time.time()))
    path = os.path.join(out, f"{a.label}-{t}.png").replace("\\", "/")
    print(t, psx.cmd("screenshot_hires", path=path), flush=True)
try:
    psx.cmd("quit"); proc.wait(60)
except Exception:
    proc.kill()
