"""Write every raw image block and palette prefix from texture pages, for hashing.

For each pag resource image block it writes:
  <src>_p<page>_m<level>_<bpp>.pix    raw PIX4/PDAT bytes (= the VRAM upload words)
  <src>_p<page>_m<level>_<bpp>.clutA  first 16 (P4) / 256 (P8) palette words
  <src>_p<page>_m<level>_<bpp>.clutB  second 16 palette words, when the CLUT holds 32
usage: python dump_raw_blocks.py <out_dir> <file> [<file> ...]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_textures import PAGE_TYPE, blocks  # noqa: E402
from shoc_resources import resources  # noqa: E402

out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
for path in sys.argv[2:]:
    src = os.path.splitext(os.path.basename(path))[0]
    for res in resources(open(path, "rb").read()):
        if res["hdr"][4:8] != PAGE_TYPE:
            continue
        page_id = struct.unpack_from("<I", res["hdr"], 8)[0]
        level, pix, bpp = 0, None, 0
        for tag, body in blocks(bytes(res["data"])):
            if tag in ("PIX4", "PDAT"):
                pix, bpp = body, (4 if tag == "PIX4" else 8)
            elif tag == "CLUT" and pix is not None:
                stem = os.path.join(out_dir, f"{src}_p{page_id:02d}_m{level}_{bpp}")
                open(stem + ".pix", "wb").write(pix)
                n = 32 if bpp == 4 else 512
                open(stem + ".clutA", "wb").write(body[:n])
                if bpp == 4 and len(body) >= 2 * n:
                    open(stem + ".clutB", "wb").write(body[n:2 * n])
                level += 1
                pix = None
