"""line.py: Parses a line of MGC script into a Command."""
import string
import re
import shlex
from functools import partial
from typing import Callable, Any, Optional
from . import commands as cmd
from . import type_validator as val
from . import logger
from .datatypes import CommandType
from .errors import BuildError


_aliases: dict[str, str] = {}
_COMMANDS: dict[str, tuple[CommandType, list[Callable[[str], Any]]]] = {
    'loc': (cmd.loc, [val.address]),
    'gci': (cmd.gci, [val.address]),
    'patch': (cmd.patch, [val.address]),
    'add': (cmd.add, [val.address]),
    'write': (cmd.write, [val.data]),
    'src': (cmd.src, [val.text]),
    'asmsrc': (cmd.asmsrc, [val.text]),
    'file': (cmd.bin, [val.text]),
    'geckocodelist':  (cmd.geckocodelist, [val.text]),
    'string': (cmd.string, [val.text]),
    'fill': (cmd.fill, [val.integer, val.data]),
    'asm': (cmd.asm, []),
    'asmend': (cmd.asmend, []),
    'c2': (cmd.c2, [val.address]),
    'c2end': (cmd.c2end, []),
    'begin': (cmd.begin, []),
    'end': (cmd.end, []),
    'echo': (cmd.echo, [val.text]),
    'macro': (cmd.macro, [val.any]),
    'macroend': (cmd.macroend, []),
    'callmacro': (cmd.call_macro, [val.any, val.integer]),
    'blockorder': (cmd.blockorder, [val.integer] * 10),
    'define': (cmd.define, [val.any, val.text])
    }


def parse(line: str, desired_command: str=None) -> Optional[CommandType]:
    """Parses the MGC script line string into a command and arguments."""
    line = line.split('#')[0]
    line = _replace_aliases(line)
    line = line.strip()
    if not line:
        return None
    cmdname = _get_command(line)
    if desired_command and cmdname != desired_command:
        return None
    if cmdname not in _COMMANDS or cmdname is None:
        raise BuildError("Invalid syntax")
    cmdtype, validators = _COMMANDS[cmdname]
    if cmdtype is cmd.write:
        args = [line]
    elif cmdtype is cmd.call_macro:
        args = line[1:].split()
        if len(args) == 1:
            args.append('1')
    else:
        args = shlex.split(line, posix=False)[1:]
    if len(args) != len(validators):
        raise BuildError(f"Expected {len(validators)} args but received {len(args)}")
    typed_args = [val(arg) for val, arg in zip(validators, args)]
    if cmdtype is cmd.define:
        _add_alias(typed_args[0], typed_args[1])
        return None
    return partial(cmdtype, *typed_args)


def _replace_aliases(line: str) -> str:
    """Replaces aliases with their defined values during parse."""
    for key, value in _aliases.items():
        line = line.replace(key, value)
    if re.search(r'\[.*\]', line):
        logger.warning("No matching alias, taking brackets literally")
    return line


def _add_alias(name: str, value: str) -> None:
    """Adds a new alias during parse if the parsed command is !define."""
    name = '[' + name + ']'
    if name in _aliases:
        logger.warning(f"Alias {name} already exists and is being overwritten")
    _aliases[name] = value


def _get_command(line: str) -> Optional[str]:
    """Gets the command name present on the current line during parse."""
    if line[0] in string.hexdigits or line[0] == '%':
        return 'write'
    if line[0] == '+':
        return 'callmacro'
    if line[0] == '!':
        return line.split()[0][1:]
    return None

