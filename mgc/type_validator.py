"""type_validator.py: Validates types from an MGC script line to ensure they
are the expected types for that command, and returns them as typed objects."""

import string
import re
from .errors import BuildError


def data(untyped: str) -> bytes:
    """Raw data, either hex (ff) or binary (%11111111)."""
    if untyped[0] in string.hexdigits:
        return _hex_string(untyped)
    elif untyped[0] == '%':
        return _binary_string(untyped)
    else:
        raise BuildError("Invalid syntax")


def _hex_string(untyped: str) -> bytes:
    """Plain hex data found in the 'data' type."""
    try:
        return bytes.fromhex(untyped)
    except ValueError:
        raise BuildError("Hex is not byte-aligned or contains invalid characters")


def _binary_string(untyped: str) -> bytes:
    """Plain binary data found in the 'data' type, prepended with %."""
    untyped = untyped[1:]
    if len(untyped) % 8 > 0:
        raise BuildError("Binary is not byte-aligned")
    untyped = re.sub(r'\s+', '', untyped) # Remove whitespace
    try:
        h = format(int(untyped, 2), 'x')
    except ValueError:
        raise BuildError("Binary contains invalid characters")
    return bytes.fromhex(h)


def integer(untyped: str) -> int:
    """An integer in decimal (19) or hex (0x13) notation."""
    try:
        if untyped[:2] == '0x':
            return int(untyped, 16)
        else:
            return int(untyped)
    except ValueError:
        raise BuildError("Invalid integer format")


def string(untyped: str) -> str:
    """A string wrapped in quotes."""
    return untyped[1:-1]
