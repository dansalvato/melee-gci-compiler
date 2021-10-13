"""line.py: Parses a line of MGC script into a Command."""
import string
import re
import shlex
from .type_validator import validate
from . import logger
from .errors import BuildError


_aliases: dict[str, str] = {}
_NOP = ('', [])

def parse(line: str, desired_command: str='') -> tuple[str, list]:
    """Parses the MGC script line string into a command and arguments."""
    line = line.split('#')[0]
    line = _replace_aliases(line)
    line = line.strip()
    if not line:
        return _NOP
    cmdname = _get_command(line)
    if desired_command and cmdname != desired_command:
        return _NOP
    if not cmdname:
        raise BuildError("Invalid syntax")
    if cmdname == 'write':
        args = [line]
    elif cmdname == 'callmacro':
        args = line[1:].split()
        if len(args) == 1:
            args.append('1')
    else:
        args = shlex.split(line, posix=False)[1:]
    typed_args = validate(cmdname, args)
    if cmdname == 'define':
        _add_alias(typed_args[0], typed_args[1])
        return _NOP
    return cmdname, typed_args


def is_command(line: str, desired_command: str) -> bool:
    """Checks if the given line contains the desired command."""
    return parse(line, desired_command) is not _NOP


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


def _get_command(line: str) -> str:
    """Gets the command name present on the current line during parse."""
    if line[0] in string.hexdigits or line[0] == '%':
        return 'write'
    if line[0] == '+':
        return 'callmacro'
    if line[0] == '!':
        return line.split()[0][1:]
    return ''

