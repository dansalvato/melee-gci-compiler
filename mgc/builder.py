"""builder.py: Builds files that are sourced during MGC script execution and
provides their data."""
from pathlib import Path
from functools import partial
from . import line
from . import asm
from .datatypes import MGCLine
from .context import Context
from .errors import BuildError


def build_binfile(filedata: bytes) -> bytes:
    """Builds a binary file and returns it in bytes."""
    return filedata


def build_asmfile(filedata: str) -> bytes:
    """Builds an ASM file and returns it in bytes."""
    compiled_asm = asm.compile_asm(filedata)
    return compiled_asm


def build_geckofile(path: Path, data: list[str]):
    """Builds a file in Gecko codelist format and returns it in bytes."""
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
    """Builds an MGC script file and returns it as a list of commands."""
    with Context(path) as c:
        start_line, end_line = _preprocess_begin_end(data)
        op_lines = []
        asm_lines = []
        asm_cmd: partial | None = None
        asm_cmd_line = 0
        for line_number, script_line in enumerate(data[start_line:end_line], start=start_line):
            if asm_cmd:
                command = line.parse(script_line, asm_cmd.func.__name__ + 'end')
                if not command:
                    asm_lines.append(script_line)
                    continue
                if asm_cmd.func.__name__ == 'c2':
                    asmdata = asm.compile_c2('\n'.join(asm_lines), asm_cmd.args[0])
                else:
                    asmdata = asm.compile_asm('\n'.join(asm_lines))
                asmcmd = partial(asm_cmd.func, asmdata)
                op_lines.append(MGCLine(asm_cmd_line, asmcmd))
                asm_cmd = None
                asm_lines.clear()
            else:
                c.line_number = line_number
                command = line.parse(script_line)
                if not command:
                    continue
                if command.func.__name__ in ['asm', 'c2']:
                    asm_cmd = command
                    asm_cmd_line = line_number
                else:
                    op_lines.append(MGCLine(line_number, command))
        if asm_cmd:
            raise BuildError("Command does not have an end specified")
        return op_lines


def _preprocess_begin_end(filedata):
    """Finds the !begin and !end lines of the MGC file."""
    start_line = 0
    end_line = len(filedata)
    for line_number, script_line in enumerate(filedata):
        if line.parse(script_line, 'begin'):
            start_line = line_number+1
            break
    for line_number, script_line in enumerate(reversed(filedata)):
        if line.parse(script_line, 'end'):
            end_line = len(filedata)-line_number-1
            break
    return start_line, end_line

