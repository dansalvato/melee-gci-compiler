"""type_validator.py: Validates types from an MGC script line to ensure they
are the expected types for that command, and returns them as typed objects."""
import string
import re
from typing import Callable
from .errors import BuildError


def validate(cmdname: str, args: list[str]) -> list:
    """Validates the arguments of a given command and returns them as typed
    args."""
    validators = _COMMANDS[cmdname]
    if len(args) != len(validators):
        raise BuildError(f"Expected {len(validators)} args but received {len(args)}")
    typed_args = [val(arg) for val, arg in zip(validators, args)]
    return typed_args


def _data(untyped: str) -> bytes:
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


def _integer(untyped: str) -> int:
    """An integer in decimal (19) or hex (0x13) notation. Used when calling macros."""
    try:
        if untyped[:2] == '0x':
            return int(untyped, 16)
        else:
            return int(untyped)
    except ValueError:
        raise BuildError("Invalid integer format")


def _address(untyped: str) -> int:
    """An integer in pure hex format, without 0x notation. Used for commands
    with memory addresses."""
    return _integer('0x' + untyped)


def _text(untyped: str) -> str:
    """A string wrapped in quotes."""
    if untyped[0] != '"' or untyped [-1] != '"':
        raise BuildError("Expected a string wrapped in quotes")
    typed = untyped[1:-1]
    if not typed:
        raise BuildError("String cannot be empty")
    return typed


def _any(untyped: str) -> str:
    """Unchecked type - any valid string."""
    return untyped


_COMMANDS: dict[str, list[Callable]] = {
    'loc': [_address],
    'gci': [_address],
    'patch': [_address],
    'add': [_address],
    'write': [_data],
    'src': [_text],
    'asmsrc': [_text],
    'file': [_text],
    'bin': [_text],
    'geckocodelist': [_text],
    'string': [_text],
    'fill': [_integer, _data],
    'asm': [],
    'asmend': [],
    'c2': [_address],
    'c2end': [],
    'begin': [],
    'end': [],
    'echo': [_text],
    'macro': [_any],
    'macroend': [],
    'callmacro': [_any, _integer],
    'blockorder': [_integer] * 10,
    'define': [_any, _text]
    }

