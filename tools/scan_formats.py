"""Peek at container headers and count known texture signatures in extracted files.

usage: python scan_formats.py <file> [<file> ...]
"""
import re
import struct
import sys

# PS1 TIM: magic 0x10, then flags with bpp in bits 0-1 and CLUT flag in bit 3.
TIM_RE = re.compile(rb"\x10\x00\x00\x00[\x00-\x03\x08\x09]\x00\x00\x00", re.S)
TAGS = [b"SHPP", b"SHPS", b"SHPI", b"SSH", b"BIGF", b"BIG4", b"C0FB", b"VIV", b"FSH", b"TIM"]


def plausible_tim(data, off):
    flags = struct.unpack_from("<I", data, off + 4)[0]
    p = off + 8
    if flags & 8:
        if p + 12 > len(data):
            return False
        clut_len, cx, cy, cw, ch = struct.unpack_from("<IHHHH", data, p)
        if clut_len != 12 + cw * ch * 2 or cw == 0 or ch == 0 or cx >= 1024 or cy >= 512:
            return False
        p += clut_len
    if p + 12 > len(data):
        return False
    img_len, x, y, w, h = struct.unpack_from("<IHHHH", data, p)
    return img_len == 12 + w * h * 2 and 0 < w <= 1024 and 0 < h <= 512 and x < 1024 and y < 512


for path in sys.argv[1:]:
    data = open(path, "rb").read()
    tims = [m.start() for m in TIM_RE.finditer(data) if plausible_tim(data, m.start())]
    tags = {t.decode(): data.count(t) for t in TAGS if data.count(t)}
    head = data[:64]
    print(f"== {path} ({len(data):,} bytes)")
    print("   head:", head[:32].hex(" "))
    print("   ascii:", "".join(chr(b) if 32 <= b < 127 else "." for b in head))
    print(f"   valid TIMs: {len(tims)}  first: {[hex(t) for t in tims[:5]]}")
    if tags:
        print("   tags:", tags)
