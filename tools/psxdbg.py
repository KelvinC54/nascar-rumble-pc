"""Tiny client for the psxrecomp debug server (debug builds, PSX_DEBUG_SERVER=1)."""
import json
import socket
import time

BIT = {"select": 0, "start": 3, "up": 4, "right": 5, "down": 6, "left": 7,
       "l2": 8, "r2": 9, "l1": 10, "r1": 11, "triangle": 12, "circle": 13,
       "cross": 14, "square": 15}


class Psx:
    def __init__(self, port=4370, timeout=60):
        self.port = port
        self.timeout = timeout
        self.next_id = 1

    def cmd(self, name, **params):
        # The server answers one request per connection, so connect each time.
        req = {"id": self.next_id, "cmd": name, **params}
        self.next_id += 1
        with socket.create_connection(("127.0.0.1", self.port), timeout=self.timeout) as sock:
            sock.sendall((json.dumps(req) + "\n").encode())
            buf = b""
            while b"\n" not in buf:
                chunk = sock.recv(1 << 20)
                if not chunk:
                    break
                buf += chunk
        return json.loads(buf.split(b"\n", 1)[0])

    def hold(self, *buttons):
        mask = 0xFFFF
        for b in buttons:
            mask &= ~(1 << BIT[b])
        return self.cmd("set_input", buttons=f"{mask:04X}")

    def release(self):
        return self.cmd("clear_input")

    def press(self, *buttons, hold_s=0.15, after_s=0.6):
        self.hold(*buttons)
        time.sleep(hold_s)
        self.release()
        time.sleep(after_s)

    def ram(self, addr=0x80000000, length=0x200000):
        r = self.cmd("read_ram", addr=f"0x{addr:08X}", len=length)
        return bytes.fromhex(r.get("data") or r.get("hex") or r.get("bytes"))
