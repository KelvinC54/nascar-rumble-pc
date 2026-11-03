"""List the resources in an EA SHOC stream (.TRK / .PSX) and reassemble their payloads.

SHOC chunk body: 8 bytes, then a sub-tag: "SHDR" starts a resource, "SDAT" carries
payload continued until the next SHDR.
usage: python shoc_resources.py <file> [out_dir]
"""
import os
import struct
import sys


def resources(data):
    pos = 0
    cur = None
    while pos + 8 <= len(data):
        raw, size = struct.unpack_from("<4sI", data, pos)
        if size < 8 or pos + size > len(data) or not raw.isalnum():
            nxt = (pos // 2048 + 1) * 2048
            if nxt >= len(data):
                break
            pos = nxt
            continue
        if raw[::-1] == b"SHOC":
            sub = data[pos + 16:pos + 20]
            body = data[pos + 20:pos + size]
            if sub == b"RDHS":            # "SHDR" reversed
                if cur:
                    yield cur
                cur = {"off": pos, "hdr": body, "data": bytearray()}
            elif sub == b"TADS" and cur:  # "SDAT" reversed
                cur["data"] += body
        pos += size
    if cur:
        yield cur


def main():
    path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else None
    data = open(path, "rb").read()
    for i, r in enumerate(resources(data)):
        hdr = r["hdr"]
        words = struct.unpack_from(f"<{len(hdr) // 4}I", hdr)
        print(f"#{i:<3} @{r['off']:08x}  data {len(r['data']):>9,}  hdr {' '.join(f'{w:08x}' for w in words[:10])}")
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            kind = words[0] if words else 0
            with open(os.path.join(out_dir, f"{i:03d}_type{kind:x}.bin"), "wb") as f:
                f.write(r["data"])


if __name__ == "__main__":
    main()
