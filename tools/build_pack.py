"""Build an HD texture pack for NASCAR Rumble from disc textures + in-game dumps.

The game hashes texture uploads exactly as stored on disc, but recolours its
palettes at runtime (shading/fog variants), so palette identities only exist in
dumps. For each dumped identity this tool rebuilds the runtime palette from the
dump's pixels, renders the WHOLE disc page with it (clean edges for the
upscaler), and later crops the upscaled page back to the dumped rectangle.

  stage     python build_pack.py stage <raw_blocks> <dumps> <work>
  finalize  python build_pack.py finalize <work> <replacements> [--resample lanczos] [--ai-gate 0.85] [--scale 2] [--merge] [--skip-ui]

stage writes <work>/staged/<key>.png (RGB, transparent texels colour-dilated),
<work>/alpha/<key>.png (exact alpha) and <work>/jobs.json. Upscale staged/ into
<work>/upscaled/ with the same filenames (e.g. Real-ESRGAN x4), then finalize.
Without upscaled/, --resample lanczos does a plain 4x resize instead.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

TOOLS = os.path.dirname(os.path.abspath(__file__))
XXH3SUM = os.path.join(TOOLS, "xxh3sum.exe")
SCALE = 4

PALETTED = re.compile(
    r"^(texupload|texpage)-(STP4|STP8|P4|P8)-([0-9A-Fa-f]{16})-([0-9A-Fa-f]{16})-"
    r"(\d+)x(\d+)-(\d+)-(\d+)-(\d+)x(\d+)-P(\d+)-(\d+)$")


def hash_blocks(raw_dir):
    paths = [os.path.join(raw_dir, n) for n in os.listdir(raw_dir)
             if n.endswith(".pix") and os.path.getsize(os.path.join(raw_dir, n))]
    out = subprocess.run([XXH3SUM], input="\n".join(paths), capture_output=True,
                         text=True, check=False).stdout
    index = {}
    for line in out.splitlines():
        h, path = line.split(" ", 1)
        index.setdefault(h.upper(), path)
    return index


def ps1_rgba(words):
    w = np.asarray(words, dtype=np.uint16)
    rgb = np.stack([(w & 31), (w >> 5) & 31, (w >> 10) & 31], axis=-1).astype(np.uint16)
    rgb = (rgb << 3) | (rgb >> 2)
    alpha = np.where(w == 0, 0, 255)[:, None]
    return np.concatenate([rgb, alpha], axis=-1).astype(np.uint8)


def load_indices(pix_path, bpp, width, height):
    raw = np.fromfile(pix_path, dtype=np.uint8)
    if bpp == 4:
        idx = np.empty(raw.size * 2, dtype=np.uint8)
        idx[0::2], idx[1::2] = raw & 15, raw >> 4
    else:
        idx = raw
    if idx.size != width * height:
        return None
    return idx.reshape(height, width)


def base_palette(pix_path, bpp):
    clut = pix_path[:-4] + ".clutA"
    n = 16 if bpp == 4 else 256
    words = np.fromfile(clut, dtype="<u2") if os.path.getsize(clut) else np.zeros(0, "<u2")
    words = np.concatenate([words, np.zeros(max(0, n - words.size), "<u2")])[:n]
    return ps1_rgba(words)


def dilate_rgb(rgba, passes=6):
    """Spread opaque colours into transparent texels so the upscaler sees no black halo."""
    rgb = rgba[..., :3].astype(np.float32)
    known = rgba[..., 3] > 0
    for _ in range(passes):
        if known.all():
            break
        acc = np.zeros_like(rgb)
        cnt = np.zeros(known.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            k = np.roll(known, (dy, dx), axis=(0, 1))
            acc += np.roll(rgb, (dy, dx), axis=(0, 1)) * k[..., None]
            cnt += k
        fill = ~known & (cnt > 0)
        rgb[fill] = acc[fill] / cnt[fill][:, None]
        known = known | fill
    return rgb.astype(np.uint8)


def stage(raw_dir, dumps_dir, work):
    index = hash_blocks(raw_dir)
    for sub in ("staged", "alpha", "known"):
        os.makedirs(os.path.join(work, sub), exist_ok=True)
    jobs, pages = [], {}
    stats = {"disc": 0, "dump_only": 0}
    for root, _, files in os.walk(dumps_dir):
        for name in files:
            if not name.lower().endswith(".png"):
                continue
            stem = name[:-4]
            dump = np.asarray(Image.open(os.path.join(root, name)).convert("RGBA"))
            m = PALETTED.match(stem)
            src = index.get(m.group(3).upper()) if m else None
            if m and src:
                mode, tex, pal = m.group(2), m.group(3).upper(), m.group(4).upper()
                bpp = 4 if mode.endswith("4") else 8
                words, rows = int(m.group(5)), int(m.group(6))
                ox, oy, w, h = (int(m.group(i)) for i in (7, 8, 9, 10))
                width = words * (4 if bpp == 4 else 2)
                key = f"{tex}_{pal}_{mode}"
                if key not in pages:
                    idx = load_indices(src, bpp, width, rows)
                    pages[key] = idx is not None and {
                        "idx": idx, "palette": base_palette(src, bpp),
                        "seen": np.zeros(16 if bpp == 4 else 256, bool)}
                page = pages[key]
                if page and dump.shape[:2] == (h, w) and ox + w <= width and oy + h <= rows:
                    # Runtime palette from the dumps: each dump only reveals the entries it uses.
                    used = page["idx"][oy:oy + h, ox:ox + w].ravel()
                    page["palette"][used] = dump.reshape(-1, 4)
                    page["seen"][used] = True
                    jobs.append({"stem": stem, "key": key, "box": [ox, oy, w, h],
                                 "src": os.path.basename(src)[:-4]})
                    stats["disc"] += 1
                    continue
            # No disc source (HUD/text built in VRAM, direct colour, ...): upscale the dump itself.
            key = "dump_" + stem
            Image.fromarray(dilate_rgb(dump), "RGB").save(os.path.join(work, "staged", key + ".png"))
            Image.fromarray(dump[..., 3], "L").save(os.path.join(work, "alpha", key + ".png"))
            jobs.append({"stem": stem, "key": key, "box": [0, 0, dump.shape[1], dump.shape[0]]})
            stats["dump_only"] += 1
    for key, page in pages.items():
        if not page:
            continue
        rgba = page["palette"][page["idx"]]
        Image.fromarray(dilate_rgb(rgba), "RGB").save(os.path.join(work, "staged", key + ".png"))
        Image.fromarray(rgba[..., 3], "L").save(os.path.join(work, "alpha", key + ".png"))
        # Texels whose palette entry no dump revealed: colour is a guess, never merge over them.
        known = page["seen"][page["idx"]].astype(np.uint8) * 255
        Image.fromarray(known, "L").save(os.path.join(work, "known", key + ".png"))
    json.dump(jobs, open(os.path.join(work, "jobs.json"), "w"), indent=0)
    print(f"jobs {len(jobs)}: {stats['disc']} rebuilt from disc pages, {stats['dump_only']} from dumps only; "
          f"{len(os.listdir(os.path.join(work, 'staged')))} images to upscale")


def merge_jobs(jobs, work):
    """One job per texture+palette identity, boxed to the union of its dumped crops.

    Polygons sample UV ranges that straddle several small dumped crops; the runtime
    then composites per draw (thousands/s, CPU bound). One covering entry per
    identity keeps each draw on the single-image fast path."""
    groups = {}
    for job in jobs:
        m = PALETTED.match(job["stem"])
        if not m or job["key"].startswith("dump_"):  # dump-only boxes are not page coords
            groups[job["stem"]] = dict(job)
            continue
        kind, mode, tex, pal, words, rows, _, _, _, _, pmin, pmax = m.groups()
        ident = (kind, mode, tex, pal, words, rows, pmin, pmax)
        ox, oy, w, h = job["box"]
        g = groups.setdefault(ident, {"key": job["key"], "box": [ox, oy, ox + w, oy + h], "ident": ident,
                                      "members": []})
        g["members"].append(job)
        b = g["box"]
        g["box"] = [min(b[0], ox), min(b[1], oy), max(b[2], ox + w), max(b[3], oy + h)]
    merged = []
    for g in groups.values():
        if "ident" not in g:
            merged.append(g)
            continue
        kind, mode, tex, pal, words, rows, pmin, pmax = g["ident"]
        x0, y0, x1, y1 = g["box"]
        known = np.asarray(Image.open(os.path.join(work, "known", g["key"] + ".png")))
        if len(g["members"]) > 1 and not known[y0:y1, x0:x1].all():
            merged.extend(g["members"])  # union would expose guessed colours
            continue
        merged.append({"key": g["key"], "box": [x0, y0, x1 - x0, y1 - y0],
                       "stem": f"{kind}-{mode}-{tex}-{pal}-{words}x{rows}-{x0}-{y0}-{x1 - x0}x{y1 - y0}-P{pmin}-{pmax}"})
    return merged


def finalize(work, out_dir, resample, gate=None, scale=None, merge=False, skip_ui=False):
    os.makedirs(out_dir, exist_ok=True)
    jobs = json.load(open(os.path.join(work, "jobs.json")))
    if skip_ui:
        # 2D UI (HUD atlas p09, demo logo p13, frontend p08/p09, VRAM-built text) looks
        # worse upscaled: glyphs thicken and bleed into neighbours. Keep it native.
        ui = re.compile(r"^(\w+_p(09|13)|FE_p0[89])_m0_")
        jobs = [j for j in jobs if not j["key"].startswith("dump_") and not ui.match(j.get("src", ""))]
    if merge:
        jobs = merge_jobs(jobs, work)
    up_dir = os.path.join(work, "upscaled")
    # ai_gate.json (tools/ai_gate.py) scores detail kept by the AI; below gate -> lanczos.
    scores = json.load(open(os.path.join(work, "ai_gate.json"))) if gate is not None else {}
    done = ai = 0
    for job in jobs:
        staged = Image.open(os.path.join(work, "staged", job["key"] + ".png"))
        up_path = os.path.join(up_dir, job["key"] + ".png")
        use_ai = os.path.exists(up_path) and (gate is None or scores.get(job["key"] + ".png", 0) >= gate)
        if use_ai:
            ai += 1
            up = Image.open(up_path).convert("RGB")
        elif resample:
            up = staged.resize((staged.width * SCALE, staged.height * SCALE), Image.LANCZOS)
        else:
            continue
        if scale and scale < up.width // staged.width:
            up = up.resize((staged.width * scale, staged.height * scale), Image.LANCZOS)
        s = up.width // staged.width
        ox, oy, w, h = job["box"]
        box = (ox * s, oy * s, (ox + w) * s, (oy + h) * s)
        alpha = Image.open(os.path.join(work, "alpha", job["key"] + ".png"))
        alpha = alpha.resize((staged.width * s, staged.height * s), Image.NEAREST).crop(box)
        rgba = up.crop(box)
        rgba.putalpha(alpha)
        rgba.save(os.path.join(out_dir, job["stem"] + ".png"))
        done += 1
    print(f"wrote {done}/{len(jobs)} replacements to {out_dir} ({ai} AI, {done - ai} lanczos)")


def main():
    cmd = sys.argv[1]
    if cmd == "stage":
        stage(*sys.argv[2:5])
    elif cmd == "finalize":
        resample = "--resample" in sys.argv
        gate = float(sys.argv[sys.argv.index("--ai-gate") + 1]) if "--ai-gate" in sys.argv else None
        scale = int(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else None
        finalize(sys.argv[2], sys.argv[3], resample, gate, scale, "--merge" in sys.argv,
                 "--skip-ui" in sys.argv)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
