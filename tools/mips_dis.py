"""Minimal MIPS R3000 disassembler for reading small game routines.

usage: python mips_dis.py <start_addr_hex> <hex_bytes_little_endian>
   or: from mips_dis import dis
"""
import struct
import sys

R = ["zero", "at", "v0", "v1", "a0", "a1", "a2", "a3", "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
     "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra"]
SPECIAL = {0x00: "sll", 0x02: "srl", 0x03: "sra", 0x04: "sllv", 0x06: "srlv", 0x07: "srav", 0x08: "jr",
           0x09: "jalr", 0x0C: "syscall", 0x10: "mfhi", 0x11: "mthi", 0x12: "mflo", 0x13: "mtlo",
           0x18: "mult", 0x19: "multu", 0x1A: "div", 0x1B: "divu", 0x20: "add", 0x21: "addu",
           0x22: "sub", 0x23: "subu", 0x24: "and", 0x25: "or", 0x26: "xor", 0x27: "nor",
           0x2A: "slt", 0x2B: "sltu"}
IMM = {0x08: "addi", 0x09: "addiu", 0x0A: "slti", 0x0B: "sltiu", 0x0C: "andi", 0x0D: "ori", 0x0E: "xori"}
MEM = {0x20: "lb", 0x21: "lh", 0x23: "lw", 0x24: "lbu", 0x25: "lhu", 0x28: "sb", 0x29: "sh", 0x2B: "sw"}
BR = {0x04: "beq", 0x05: "bne", 0x06: "blez", 0x07: "bgtz"}


def dis(addr, word):
    op, rs, rt, rd = word >> 26, (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31
    sh, fn, imm = (word >> 6) & 31, word & 63, word & 0xFFFF
    simm = imm - 0x10000 if imm & 0x8000 else imm
    if word == 0:
        return "nop"
    if op == 0:
        m = SPECIAL.get(fn, f"special.{fn:#x}")
        if fn in (0, 2, 3):
            return f"{m} {R[rd]}, {R[rt]}, {sh}"
        if fn == 8:
            return f"jr {R[rs]}"
        if fn == 9:
            return f"jalr {R[rd]}, {R[rs]}"
        if fn in (0x10, 0x12):
            return f"{m} {R[rd]}"
        if fn in (0x18, 0x19, 0x1A, 0x1B):
            return f"{m} {R[rs]}, {R[rt]}"
        return f"{m} {R[rd]}, {R[rs]}, {R[rt]}"
    if op in (2, 3):
        return f"{'j' if op == 2 else 'jal'} 0x{(addr & 0xF0000000) | ((word & 0x3FFFFFF) << 2):08X}"
    if op == 1:
        return f"{['bltz', 'bgez'][rt & 1]} {R[rs]}, 0x{addr + 4 + (simm << 2):08X}"
    if op in BR:
        return f"{BR[op]} {R[rs]}, {R[rt]}, 0x{addr + 4 + (simm << 2):08X}"
    if op == 0x0F:
        return f"lui {R[rt]}, 0x{imm:04X}"
    if op in IMM:
        return f"{IMM[op]} {R[rt]}, {R[rs]}, {simm if op in (8, 9, 0xA, 0xB) else hex(imm)}"
    if op in MEM:
        return f"{MEM[op]} {R[rt]}, {simm}({R[rs]})"
    return f"op.{op:#x} {word:08X}"


if __name__ == "__main__":
    start = int(sys.argv[1], 16)
    data = bytes.fromhex(sys.argv[2])
    for i in range(0, len(data) - 3, 4):
        w = struct.unpack_from("<I", data, i)[0]
        print(f"{start + i:08X}  {w:08X}  {dis(start + i, w)}")
