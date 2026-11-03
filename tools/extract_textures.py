"""Extract NASCAR Rumble textures from SHOC containers (.TRK / .PSX) to PNG.

Texture pages are "pag" resources holding a mip chain of image blocks, each
followed by its palette:
  PIX4 (4bpp) / PDAT (8bpp) image, then CLUT (PS1 15-bit colours).
Only the full-size level of each chain is written by default (--mips for all).

usage: python extract_textures.py <out_dir> <file.TRK> [<file> ...] [--mips]
"""
import math
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shoc_resources import resources  # noqa: E402

PAGE_TYPE = b"gapC"  # "Cpag" stored reversed


def write_png(path, w, h, rgba):
    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    rows = b"".join(b"\x00" + rgba[y * w * 4:(y + 1) * w * 4] for y in range(h))
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(rows, 9)))
        f.write(chunk(b"IEND", b""))


def ps1_colour(c):
    r, g, b = (c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3
    # Colour 0x0000 is transparent on PS1 hardware; everything else is drawn.
    return bytes((r | r >> 5, g | g >> 5, b | b >> 5, 0 if c == 0 else 255))


def blocks(page):
    pos = 0
    while pos + 8 <= len(page):
        raw, size = struct.unpack_from("<4sI", page, pos)
        if size < 8 or pos + size > len(page):
            return
        yield raw[::-1].decode("ascii", "replace"), page[pos + 8:pos + size]
        pos += size


def decode_pages(page):
    """Yield (bpp, w, h, rgba) for each image + palette pair in a page."""
    pending = None
    for tag, body in blocks(page):
        if tag in ("PIX4", "PDAT"):
            pending = (4 if tag == "PIX4" else 8, body)
        elif tag == "CLUT" and pending:
            bpp, pix = pending
            pending = None
            pal = [ps1_colour(c) for c in struct.unpack_from(f"<{len(body) // 2}H", body)]
            count = len(pix) * (2 if bpp == 4 else 1)
            side = int(math.isqrt(count))
            w, h = (side, side) if side * side == count else (256, count // 256)
            out = bytearray()
            for byte in pix:
                idxs = (byte & 15, byte >> 4) if bpp == 4 else (byte,)
                for i in idxs:
                    out += pal[i] if i < len(pal) else b"\xff\x00\xff\xff"
            yield bpp, w, h, bytes(out)


def main():
    args = [a for a in sys.argv[1:] if a != "--mips"]
    all_mips = "--mips" in sys.argv
    out_dir, files = args[0], args[1:]
    total = 0
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        dst = os.path.join(out_dir, name)
        os.makedirs(dst, exist_ok=True)
        data = open(path, "rb").read()
        n = 0
        for res in resources(data):
            if res["hdr"][4:8] != PAGE_TYPE:
                continue
            page_id = struct.unpack_from("<I", res["hdr"], 8)[0]
            for level, (bpp, w, h, rgba) in enumerate(decode_pages(bytes(res["data"]))):
                if level and not all_mips:
                    break
                write_png(os.path.join(dst, f"page{page_id:02d}_mip{level}_{w}x{h}_{bpp}bpp.png"), w, h, rgba)
                n += 1
        print(f"{name}: {n} textures")
        total += n
    print(f"total {total}")


if __name__ == "__main__":
    main()
