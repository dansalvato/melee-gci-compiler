"""builder.py: A class that stores the data from an MGC file as a list of
Operations to execute."""
from pathlib import Path
from functools import partial
from . import line
from . import asm
from . import commands as cmd
from .datatypes import MGCLine
from .datatypes import CommandType
from .context import Context
from .errors import *


def build_binfile(filedata):
    return filedata


def build_asmfile(filedata):
    compiled_asm = asm.compile_asm(filedata)
    return bytearray.fromhex(compiled_asm)


def build_geckofile(path: Path, data: list[str]):
    with Context(path) as c:
        header = bytes.fromhex('00d0c0de00d0c0de')
        footer = bytes.fromhex('f000000000000000')
        bytedata = bytes()
        for line_number, line in enumerate(data):
            c.line_number = line_number
            if line[0] != '*':
                continue
            line = line[1:]
            try:
                bytedata += bytes.fromhex(line)
            except ValueError:
                raise BuildError("Invalid Gecko code line")
    return header + bytedata + footer


def build_mgcfile(path: Path, data: list[str]) -> list[MGCLine]:
    with Context(path) as c:
        start_line, end_line = _preprocess_begin_end(data)
        op_lines = _preprocess_op_lines(data, start_line, end_line, c)
        return op_lines


def _preprocess_op_lines(data: list[str], start_line: int, end_line: int, c: Context) -> list[MGCLine]:
    op_lines = []
    open_tag: partial | None = None
    for line_number, script_line in enumerate(data[start_line:end_line], start=start_line):
        if open_tag:
            command = line.parse(script_line, open_tag.func.__name__ + 'end')
            if not command:
                continue
            # TODO: Compile ASM block
            open_tag = None
        else:
            command = line.parse(script_line)
            if not command:
                continue
            if command.func.__name__ in ['asm', 'c2']:
                open_tag = command
            c.line_number = line_number
            op_lines.append(MGCLine(line_number, command))
    if open_tag:
        raise BuildError("Command does not have an end specified")
    return op_lines


def _preprocess_begin_end(filedata):
    start_line = 0
    end_line = len(filedata)
    for line_number, line in enumerate(filedata):
        if line.strip() == '!begin':
            start_line = line_number+1
            break
    for line_number, line in enumerate(reversed(filedata)):
        if line.strip() == '!end':
            end_line = len(filedata)-line_number-1
            break
    return start_line, end_line

