"""Walk the reversed-FourCC chunk container used by NASCAR Rumble .TRK/.PSX files.

Each chunk: 4-byte tag (stored reversed), u32 size including the 8-byte header.
usage: python walk_chunks.py <file> [max_chunks]
"""
import collections
import struct
import sys

path = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 60
data = open(path, "rb").read()

pos = 0
shown = 0
totals = collections.Counter()
sizes = collections.defaultdict(int)
while pos + 8 <= len(data):
    raw, size = struct.unpack_from("<4sI", data, pos)
    tag = raw[::-1].decode("ascii", "replace")
    if size < 8 or pos + size > len(data) or not raw.isalnum():
        # Padding to the sector boundary, or the end of the chunk stream.
        nxt = (pos // 2048 + 1) * 2048
        if nxt >= len(data):
            break
        if shown < limit:
            print(f"{pos:08x}  -- skip to {nxt:08x} (raw {raw!r} size {size:#x})")
        pos = nxt
        continue
    totals[tag] += 1
    sizes[tag] += size
    if shown < limit:
        body = data[pos + 8:pos + 24]
        print(f"{pos:08x}  {tag}  {size:>9,}  {body.hex(' ')}")
        shown += 1
    pos += size

print("\nchunk totals:")
for tag, n in totals.most_common():
    print(f"  {tag}  x{n:<5} {sizes[tag]:>11,} bytes")
