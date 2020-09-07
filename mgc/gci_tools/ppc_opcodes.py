"""ppc_opcodes.py: Python implementations of the PPC opcodes needed for GCI encode/decode functions."""

def mask(mb: int, me: int) -> int:
    if mb >= 32 or me >= 32:
        raise ValueError("Argument values must be between 0 and 31.")
    x = 0xffffffff >> mb
    y = (0xffffffff << 31 - me) & 0xffffffff  # The & truncates to 32-bit
    if mb <= me: return x & y
    else: return x | y

def rotl(rx: int, sh: int) -> int:
    if sh >= 32:
        raise ValueError("Shift amount must be between 0 and 31.")
    return ((rx << sh) & 0xffffffff) | (rx >> ((32 - sh) & 31))

def rlwinm(rs: int, sh: int, mb: int, me: int) -> int:
    return rotl(rs, sh) & mask(mb, me)

def rlwimi(ra: int, rs: int, sh: int, mb: int, me: int) -> int:
    m = mask(mb, me)
    r = rotl(rs, sh)
    return (r & m) | (ra & ~m)