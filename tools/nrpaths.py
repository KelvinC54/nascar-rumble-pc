"""Workspace paths shared by the tools.

ROOT is the workspace folder (this repo's checkout, which also holds toolchain/ and
nascar-rumble-recomp/); override with NR_ROOT. DISC is your own dump's .cue, read from
the project's game.toml [game] disc unless NR_DISC is set.
"""
import os
import re

ROOT = os.environ.get("NR_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "nascar-rumble-recomp")
TOOLCHAIN_BIN = os.path.join(ROOT, "toolchain", "bin")


def _disc_from_game_toml():
    try:
        text = open(os.path.join(PROJECT, "game.toml"), encoding="utf-8").read()
    except OSError:
        return ""
    m = re.search(r'^disc\s*=\s*"(.*)"', text, re.M)
    return m.group(1).replace("\\\\", "\\") if m else ""


DISC = os.environ.get("NR_DISC") or _disc_from_game_toml()
