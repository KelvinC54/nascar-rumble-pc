"""Score how much detail the AI upscale lost per texture: downscale AI 4x back to 1x and
compare high-frequency energy with the original. Writes <work>/ai_gate.json {name: ratio}.

usage: python ai_gate.py <work>
ratio ~1 = detail kept; low ratio = AI smeared it (foliage), use lanczos instead.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

work = sys.argv[1]
staged, upscaled = os.path.join(work, "staged"), os.path.join(work, "upscaled")


def hf(img):
    a = np.asarray(img.convert("L"), dtype=np.float32)
    b = np.asarray(img.convert("L").filter(ImageFilter.GaussianBlur(1)), dtype=np.float32)
    return float(np.abs(a - b).mean())


scores = {}
for name in os.listdir(upscaled):
    src = Image.open(os.path.join(staged, name)).convert("RGB")
    ai = Image.open(os.path.join(upscaled, name)).convert("RGB").resize(src.size, Image.BOX)
    base = hf(src)
    scores[name] = hf(ai) / base if base > 0.5 else 1.0
json.dump(scores, open(os.path.join(work, "ai_gate.json"), "w"), indent=0)
r = np.array(list(scores.values()))
for t in (0.5, 0.6, 0.7, 0.8):
    print(f"ratio < {t}: {(r < t).sum()} of {len(r)}")
