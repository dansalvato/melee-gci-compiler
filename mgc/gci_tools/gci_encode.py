#!usr/bin/env python
"""gci_encode.py: Encodes and decodes bytes in a Melee GCI file."""

from .ppc_opcodes import *

CHECKSUM_SEED = bytes([
    0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
    0xFE, 0xDC, 0xBA, 0x98, 0x76, 0x54, 0x32, 0x10
    ])

UNK_ARR = [
    0x00000026,
    0x000000FF,
    0x000000E8,
    0x000000EF,
    0x00000042,
    0x000000D6,
    0x00000001,
    0x00000054,
    0x00000014,
    0x000000A3,
    0x00000080,
    0x000000FD,
    0x0000006E,
    ]

def decode_byte(prev_byte: int, current_byte: int) -> int:
    """Decodes a byte from an encoded GCI."""
    r0 = r3 = r4 = r5 = r6 = r7 = 0

    if prev_byte == 0:
        r5 = 0x92492493
        r5 = ((r5 * prev_byte) >> 32) & 0xffffffff
    else:
        r5 = ~0x92492493 & 0xffffffff
        r5 = (~(r5 * prev_byte) >> 32) & 0xffffffff

    r5 = (r5 + prev_byte) & 0xff
    r5 = r5 >> 2
    r6 = rlwinm(r5, 1, 31, 31)
    r5 = r5 + r6
    r5 = (r5 * 7) & 0xffffffff
    r7 = (prev_byte - r5) & 0xffffffff

    if r7 == 0:
        r5 = rlwinm(current_byte, 1, 29, 29);
        r5 = rlwimi(r5, current_byte, 0, 31, 31);
        r5 = rlwimi(r5, current_byte, 2, 27, 27);
        r5 = rlwimi(r5, current_byte, 3, 25, 25);
        r5 = rlwimi(r5, current_byte, 29, 30, 30);
        r5 = rlwimi(r5, current_byte, 30, 28, 28);
        r5 = rlwimi(r5, current_byte, 31, 26, 26);
        r5 = rlwimi(r5, current_byte, 0, 24, 24);
        r4 = rlwinm(r5, 0, 24, 31);
    elif r7 == 1:
        r5 = rlwinm(current_byte, 6, 24, 24);
        r5 = rlwimi(r5, current_byte, 1, 30, 30);
        r5 = rlwimi(r5, current_byte, 0, 29, 29);
        r5 = rlwimi(r5, current_byte, 29, 31, 31);
        r5 = rlwimi(r5, current_byte, 1, 26, 26);
        r5 = rlwimi(r5, current_byte, 31, 27, 27);
        r5 = rlwimi(r5, current_byte, 29, 28, 28);
        r5 = rlwimi(r5, current_byte, 31, 25, 25);
        r4 = rlwinm(r5, 0, 24, 31);
    elif r7 == 2:
        r5 = rlwinm(current_byte, 2, 28, 28);
        r5 = rlwimi(r5, current_byte, 2, 29, 29);
        r5 = rlwimi(r5, current_byte, 4, 25, 25);
        r5 = rlwimi(r5, current_byte, 1, 27, 27);
        r5 = rlwimi(r5, current_byte, 3, 24, 24);
        r5 = rlwimi(r5, current_byte, 28, 30, 30);
        r5 = rlwimi(r5, current_byte, 26, 31, 31);
        r5 = rlwimi(r5, current_byte, 30, 26, 26);
        r4 = rlwinm(r5, 0, 24, 31);
    elif r7 == 3:
        r5 = rlwinm(current_byte, 31, 31, 31);
        r5 = rlwimi(r5, current_byte, 4, 27, 27);
        r5 = rlwimi(r5, current_byte, 3, 26, 26);
        r5 = rlwimi(r5, current_byte, 30, 30, 30);
        r5 = rlwimi(r5, current_byte, 31, 28, 28);
        r5 = rlwimi(r5, current_byte, 1, 25, 25);
        r5 = rlwimi(r5, current_byte, 1, 24, 24);
        r5 = rlwimi(r5, current_byte, 27, 29, 29);
        r4 = rlwinm(r5, 0, 24, 31);
    elif r7 == 4:
        r5 = rlwinm(current_byte, 4, 26, 26);
        r5 = rlwimi(r5, current_byte, 3, 28, 28);
        r5 = rlwimi(r5, current_byte, 31, 30, 30);
        r5 = rlwimi(r5, current_byte, 4, 24, 24);
        r5 = rlwimi(r5, current_byte, 2, 25, 25);
        r5 = rlwimi(r5, current_byte, 29, 29, 29);
        r5 = rlwimi(r5, current_byte, 30, 27, 27);
        r5 = rlwimi(r5, current_byte, 25, 31, 31);
        r4 = rlwinm(r5, 0, 24, 31);
    elif r7 == 5:
        r5 = rlwinm(current_byte, 5, 25, 25);
        r5 = rlwimi(r5, current_byte, 5, 26, 26);
        r5 = rlwimi(r5, current_byte, 5, 24, 24);
        r5 = rlwimi(r5, current_byte, 0, 28, 28);
        r5 = rlwimi(r5, current_byte, 30, 29, 29);
        r5 = rlwimi(r5, current_byte, 27, 31, 31);
        r5 = rlwimi(r5, current_byte, 27, 30, 30);
        r5 = rlwimi(r5, current_byte, 29, 27, 27);
        r4 = rlwinm(r5, 0, 24, 31);
    elif r7 == 6:
        r5 = rlwinm(current_byte, 0, 30, 30);
        r5 = rlwimi(r5, current_byte, 6, 25, 25);
        r5 = rlwimi(r5, current_byte, 30, 31, 31);
        r5 = rlwimi(r5, current_byte, 2, 26, 26);
        r5 = rlwimi(r5, current_byte, 0, 27, 27);
        r5 = rlwimi(r5, current_byte, 2, 24, 24);
        r5 = rlwimi(r5, current_byte, 28, 29, 29);
        r5 = rlwimi(r5, current_byte, 28, 28, 28);
        r4 = rlwinm(r5, 0, 24, 31);
    else:
        raise ValueError("r7 should be no greater than 6")

    r5 = 0x4ec4ec4f
    r5 = ((r5 * prev_byte) >> 32) & 0xffffffff
    r5 = r5 >> 2
    r6 = rlwinm(r5, 1, 31, 31)
    r5 = r5 + r6
    r5 = r5 * 13
    r0 = (prev_byte - r5) & 0xff
    r6 = rlwinm(r0, 2, 0, 29)
    r0 = UNK_ARR[int(r6 / 4)]
    r4 = r4 ^ r0
    r4 = (r4 ^ prev_byte) & 0xff
    r3 = r4 + 0
    return r3



def encode_byte(prev_byte: int, current_byte: int) -> int:
    """Encodes a byte from a decoded GCI."""
    r0 = r3 = r5 = 0

    r5 = ((0x4ec4ec4f * prev_byte) >> 32) & 0xffffffff

    if prev_byte == 0:
        r0 = 0x92492493
        r0 = ((r0 * prev_byte) >> 32) & 0xffffffff
    else:
        r0 = ~0x92492493 & 0xffffffff
        r0 = (~(r0 * prev_byte) >> 32) & 0xffffffff

    r3 = r5 >> 2
    r5 = rlwinm(r3, 1, 31, 31)
    r0 = (r0 + prev_byte) & 0xff
    r3 = r3 + r5
    r0 = r0 >> 2
    r5 = r3 * 13
    r3 = rlwinm(r0, 1, 31, 31)
    r0 = r0 + r3
    r0 = r0 * 7
    r5 = (prev_byte - r5) & 0xff
    r0 = (prev_byte - r0) & 0xff
    r5 = rlwinm(r5, 2, 0, 29)

    r5 = UNK_ARR[int(r5 / 4)]

    r3 = prev_byte ^ current_byte
    r3 = r3 ^ r5

    if r0 > 6:
        raise ValueError("r0 should be no greater than 6")
    r0 = rlwinm(r0, 2, 0, 29)
    if r0 == 0x0:
            r0 = rlwinm(r3, 3, 27, 27);
            r0 = rlwimi(r0, r3, 0, 31, 31);
            r0 = rlwimi(r0, r3, 31, 30, 30);
            r0 = rlwimi(r0, r3, 2, 26, 26);
            r0 = rlwimi(r0, r3, 30, 29, 29);
            r0 = rlwimi(r0, r3, 1, 25, 25);
            r0 = rlwimi(r0, r3, 29, 28, 28);
            r0 = rlwimi(r0, r3, 0, 24, 24);
            r3 = rlwinm(r0, 0, 24, 31);
    elif r0 == 0x4:
            r0 = rlwinm(r3, 31, 31, 31);
            r0 = rlwimi(r0, r3, 3, 28, 28);
            r0 = rlwimi(r0, r3, 0, 29, 29);
            r0 = rlwimi(r0, r3, 3, 25, 25);
            r0 = rlwimi(r0, r3, 1, 26, 26);
            r0 = rlwimi(r0, r3, 31, 27, 27);
            r0 = rlwimi(r0, r3, 1, 24, 24);
            r0 = rlwimi(r0, r3, 26, 30, 30);
            r3 = rlwinm(r0, 0, 24, 31);
    elif r0 == 0x8:
            r0 = rlwinm(r3, 4, 26, 26);
            r0 = rlwimi(r0, r3, 6, 25, 25);
            r0 = rlwimi(r0, r3, 30, 31, 31);
            r0 = rlwimi(r0, r3, 30, 30, 30);
            r0 = rlwimi(r0, r3, 31, 28, 28);
            r0 = rlwimi(r0, r3, 2, 24, 24);
            r0 = rlwimi(r0, r3, 28, 29, 29);
            r0 = rlwimi(r0, r3, 29, 27, 27);
            r3 = rlwinm(r0, 0, 24, 31);
    elif r0 == 0xc:
            r0 = rlwinm(r3, 2, 28, 28);
            r0 = rlwimi(r0, r3, 1, 30, 30);
            r0 = rlwimi(r0, r3, 5, 24, 24);
            r0 = rlwimi(r0, r3, 1, 27, 27);
            r0 = rlwimi(r0, r3, 28, 31, 31);
            r0 = rlwimi(r0, r3, 29, 29, 29);
            r0 = rlwimi(r0, r3, 31, 26, 26);
            r0 = rlwimi(r0, r3, 31, 25, 25);
            r3 = rlwinm(r0, 0, 24, 31);
    elif r0 == 0x10:
            r0 = rlwinm(r3, 1, 29, 29);
            r0 = rlwimi(r0, r3, 7, 24, 24);
            r0 = rlwimi(r0, r3, 3, 26, 26);
            r0 = rlwimi(r0, r3, 29, 31, 31);
            r0 = rlwimi(r0, r3, 2, 25, 25);
            r0 = rlwimi(r0, r3, 28, 30, 30);
            r0 = rlwimi(r0, r3, 30, 27, 27);
            r0 = rlwimi(r0, r3, 28, 28, 28);
            r3 = rlwinm(r0, 0, 24, 31);
    elif r0 == 0x14:
            r0 = rlwinm(r3, 5, 25, 25);
            r0 = rlwimi(r0, r3, 5, 26, 26);
            r0 = rlwimi(r0, r3, 2, 27, 27);
            r0 = rlwimi(r0, r3, 0, 28, 28);
            r0 = rlwimi(r0, r3, 3, 24, 24);
            r0 = rlwimi(r0, r3, 27, 31, 31);
            r0 = rlwimi(r0, r3, 27, 30, 30);
            r0 = rlwimi(r0, r3, 27, 29, 29);
            r3 = rlwinm(r0, 0, 24, 31);
    elif r0 == 0x18:
            r0 = rlwinm(r3, 0, 30, 30);
            r0 = rlwimi(r0, r3, 2, 29, 29);
            r0 = rlwimi(r0, r3, 4, 25, 25);
            r0 = rlwimi(r0, r3, 4, 24, 24);
            r0 = rlwimi(r0, r3, 0, 27, 27);
            r0 = rlwimi(r0, r3, 30, 28, 28);
            r0 = rlwimi(r0, r3, 26, 31, 31);
            r0 = rlwimi(r0, r3, 30, 26, 26);
            r3 = rlwinm(r0, 0, 24, 31);
    return r3
