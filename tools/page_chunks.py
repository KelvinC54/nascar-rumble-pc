"""List the sub-blocks of a NASCAR Rumble texture page (pag resource payload).

Sub-block: reversed FourCC + u32 size including the 8-byte header.
usage: python page_chunks.py <page.bin> [<page.bin> ...]
"""
import struct
import sys

for path in sys.argv[1:]:
    data = open(path, "rb").read()
    print(f"== {path} ({len(data):,} bytes)")
    pos = 0
    while pos + 8 <= len(data):
        raw, size = struct.unpack_from("<4sI", data, pos)
        tag = raw[::-1].decode("ascii", "replace")
        if size < 8 or pos + size > len(data):
            print(f"   {pos:06x}  ?? {raw.hex()} size {size:#x} -- stop")
            break
        body = data[pos + 8:pos + 8 + 24]
        print(f"   {pos:06x}  {tag}  {size:>7,}  {body.hex(' ')}")
        pos += size
