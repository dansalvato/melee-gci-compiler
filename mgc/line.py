"""line.py: Parses a line of MGC script into a Command."""
import string
import re
import shlex
from functools import partial
from . import commands as cmd
from . import type_validator as val
from . import logger
from .datatypes import CommandType, CommandArgsType
from .errors import BuildError


_aliases: dict[str, str] = {}
_COMMANDS: dict[str, tuple[CommandType, list[CommandArgsType]]] = {
    'loc': (cmd.loc, [val.address]),
    'gci': (cmd.gci, [val.address]),
    'patch': (cmd.patch, [val.address]),
    'add': (cmd.add, [val.address]),
    'write': (cmd.write, [val.data]),
    'src': (cmd.src, [val.string]),
    'asmsrc': (cmd.asmsrc, [val.string]),
    'file': (cmd.bin, [val.string]),
    'geckocodelist':  (cmd.geckocodelist, [val.string]),
    'string': (cmd.string, [val.string]),
    'fill': (cmd.fill, [val.integer, val.data]),
    'asm': (cmd.asm, [val.any]),
    'asmend': (cmd.asmend, []),
    'c2': (cmd.c2, [val.address, val.any]),
    'c2end': (cmd.c2end, []),
    'begin': (cmd.begin, []),
    'end': (cmd.end, []),
    'echo': (cmd.echo, [val.string]),
    'macro': (cmd.macro, [val.any]),
    'macroend': (cmd.macroend, []),
    'callmacro': (cmd.call_macro, [val.any, val.integer]),
    'blockorder': (cmd.blockorder, [val.integer] * 10),
    'define': (cmd.define, [val.any, val.string])
    }


def parse(line: str) -> CommandType | None:
    """Parses the MGC script line string into a command and arguments."""
    line = line.split('#')[0]
    line = _replace_aliases(line)
    line = line.strip()
    if not line:
        return None
    cmdtype, validators = _get_command(line)
    if cmdtype is cmd.write:
        args = line
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
    for key, value in _aliases.items():
        line.replace(key, value)
    if re.search(r'\[.*\]', line):
        logger.warning("No matching alias, taking brackets literally")
    return line


def _add_alias(name: str, value: str) -> None:
    name = '[' + name + ']'
    if name in _aliases:
        logger.warning(f"Alias {name} already exists and is being overwritten")
    _aliases[name] = value


def _get_command(line: str) -> tuple[CommandType, list[CommandArgsType]]:
    if line[0] in string.hexdigits or line[0] == '%':
        return _COMMANDS['write']
    if line[0] == '+':
        return _COMMANDS['callmacro']
    if line[0] == '!':
        cmdname = line.split()[0][1:]
        if cmdname not in _COMMANDS:
            raise BuildError("Invalid command name")
        return _COMMANDS[line.split()[0][1:]]
    raise BuildError("Invalid syntax")

