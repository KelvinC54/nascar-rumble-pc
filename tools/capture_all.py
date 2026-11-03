"""Capture HD-texture dumps for every demo location/track, headless, one run each.

Runs the debug build with --headless-opengl, the Demo Track Picker mod set to
each (location, track), and HD texture dumping into the release build's pack.
Each run idles into the attract demo, records for --seconds, then quits cleanly.
usage: python capture_all.py [--seconds 240] [--locations 0-7] [--tracks 0-2]
"""
import argparse
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psxdbg import Psx  # noqa: E402
import nrpaths  # noqa: E402

ROOT = nrpaths.ROOT
DEBUG = os.path.join(nrpaths.PROJECT, "build-debug")
PACK = os.path.join(nrpaths.PROJECT, "build-release", "mods", "texture-packs", "SLUS-01068")
DISC = nrpaths.DISC

STATE = """format_version = 2
[[package]]
id = "nascar.demo-track"
version = "1.0.0"
[[package]]
id = "psx.enhancement.hd-textures"
version = "1.0.0"
[[feature]]
package_id = "nascar.demo-track"
id = "demo-track"
enabled = true
[feature.values]
location = {loc}
track = {trk}
[[feature]]
package_id = "psx.enhancement.hd-textures"
id = "hd-textures"
enabled = true
[feature.values]
replacements = false
dump = true
[feature.resources]
pack = "{pack}"
"""


def span(text):
    lo, _, hi = text.partition("-")
    return range(int(lo), int(hi or lo) + 1)


def count_dumps():
    return sum(len(f) for _, _, f in os.walk(os.path.join(PACK, "dumps")))


def run_one(loc, trk, seconds):
    with open(os.path.join(DEBUG, "mods", "state.toml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(STATE.format(loc=loc, trk=trk, pack=PACK.replace("\\", "/")))
    env = dict(os.environ, PSX_DEBUG_SERVER="1", PSX_INTERNAL_RESOLUTION="1x")
    log = open(os.path.join(DEBUG, f"capture_{loc}_{trk}.log"), "w")
    proc = subprocess.Popen(
        [os.path.join(DEBUG, "NascarRumble_Recompiled.exe"), "--no-launcher", "--headless-opengl",
         "--game", "game.toml", "--disc", DISC, "--debug-port", "4370"],
        cwd=DEBUG, env=env, stdout=log, stderr=subprocess.STDOUT)
    psx = Psx()
    seen = None
    deadline = time.time() + seconds
    while time.time() < deadline and proc.poll() is None:
        time.sleep(10)
        try:
            seen = tuple(psx.ram(0x800B7194, 2))
        except OSError:
            pass
    status = "crashed" if proc.poll() is not None else "ok"
    if proc.poll() is None:
        try:
            psx.cmd("quit")
        except OSError:
            pass
        try:
            proc.wait(60)
        except subprocess.TimeoutExpired:
            proc.kill()
            status = "killed"
    log.close()
    return status, seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=240)
    ap.add_argument("--locations", default="0-7")
    ap.add_argument("--tracks", default="0-2")
    a = ap.parse_args()
    for loc in span(a.locations):
        for trk in span(a.tracks):
            before = count_dumps()
            t0 = time.time()
            status, seen = run_one(loc, trk, a.seconds)
            print(f"location {loc} track {trk}: {status}, demo var {seen}, "
                  f"+{count_dumps() - before} dumps, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
