"""Extract the ISO9660 filesystem from a MODE2/2352 PS1 .bin.

usage: python extract_disc.py <game.bin> <out_dir>
"""
import os
import struct
import sys

SECTOR = 2352
USER_OFF = 24  # sync(12) + header(4) + subheader(8)


def read_sector(f, lba):
    f.seek(lba * SECTOR + USER_OFF)
    return f.read(2048)


def read_extent(f, lba, size):
    out = bytearray()
    while len(out) < size:
        out += read_sector(f, lba)
        lba += 1
    return bytes(out[:size])


def walk(f, lba, size, path, out_dir, listing):
    data = read_extent(f, lba, size)
    pos = 0
    while pos < len(data):
        rec_len = data[pos]
        if rec_len == 0:
            pos = (pos // 2048 + 1) * 2048  # records never span sectors
            continue
        rec = data[pos:pos + rec_len]
        ext_lba = struct.unpack_from("<I", rec, 2)[0]
        ext_size = struct.unpack_from("<I", rec, 10)[0]
        flags = rec[25]
        name_len = rec[32]
        name = rec[33:33 + name_len]
        pos += rec_len
        if name in (b"\x00", b"\x01"):
            continue
        name = name.decode("ascii", "replace").split(";")[0]
        rel = f"{path}/{name}" if path else name
        if flags & 2:
            os.makedirs(os.path.join(out_dir, rel), exist_ok=True)
            walk(f, ext_lba, ext_size, rel, out_dir, listing)
        else:
            dst = os.path.join(out_dir, rel)
            with open(dst, "wb") as o:
                o.write(read_extent(f, ext_lba, ext_size))
            listing.append((rel, ext_size, ext_lba))


def main():
    src, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    listing = []
    with open(src, "rb") as f:
        pvd = read_sector(f, 16)
        assert pvd[1:6] == b"CD001", "no ISO9660 primary volume descriptor"
        root = pvd[156:156 + 34]
        walk(f, struct.unpack_from("<I", root, 2)[0],
             struct.unpack_from("<I", root, 10)[0], "", out_dir, listing)
    for rel, size, lba in sorted(listing):
        print(f"{size:>11,}  {rel}")
    print(f"{len(listing)} files")


if __name__ == "__main__":
    main()
