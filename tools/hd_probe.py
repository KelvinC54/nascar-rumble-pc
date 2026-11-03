"""Sample HD-texture counters in a demo race on the debug build (headless).

usage: python hd_probe.py [--seconds 150] [--pack <dir>]
Prints per-10s deltas of hd_textures counters plus guest frame rate.
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psxdbg import Psx  # noqa: E402
import capture_all  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--seconds", type=int, default=150)
ap.add_argument("--pack", default=capture_all.PACK)
a = ap.parse_args()
state = capture_all.STATE.format(loc=0, trk=1, pack=a.pack.replace("\\", "/"))
state = state.replace("replacements = false\ndump = true", "replacements = true\ndump = false")
with open(os.path.join(capture_all.DEBUG, "mods", "state.toml"), "w", newline="\n") as f:
    f.write(state)
env = dict(os.environ, PSX_DEBUG_SERVER="1", PSX_INTERNAL_RESOLUTION="1x")
log = open(os.path.join(capture_all.DEBUG, "hd_probe.log"), "w")
proc = subprocess.Popen([os.path.join(capture_all.DEBUG, "NascarRumble_Recompiled.exe"), "--no-launcher",
                         "--headless-opengl", "--game", "game.toml", "--disc", capture_all.DISC,
                         "--debug-port", "4370"], cwd=capture_all.DEBUG, env=env, stdout=log, stderr=subprocess.STDOUT)
psx = Psx()
keys = ["draw_queries", "matched_draws", "ready_draws", "applied_draws", "composition_hits",
        "composition_builds", "composition_pixels", "gl_uploads", "gl_evictions", "decoded_images", "decode_evictions"]
prev = None
end = time.time() + a.seconds
while time.time() < end:
    time.sleep(10)
    try:
        r = psx.cmd("hd_textures")
        fr = psx.cmd("status")
    except OSError:
        continue
    cur = {k: r.get(k, 0) for k in keys}
    cur["frame"] = fr.get("frame", fr.get("frames", 0))
    if prev:
        print(" ".join(f"{k}=+{cur[k] - prev[k]}" for k in cur), flush=True)
    prev = cur
try:
    psx.cmd("quit"); proc.wait(60)
except Exception:
    proc.kill()
