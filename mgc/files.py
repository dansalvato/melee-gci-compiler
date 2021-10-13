"""files.py: Loads and builds files when sourced by the MGC script."""
from pathlib import Path
from functools import partial
from . import logger
from . import line
from . import asm
from .datatypes import MGCLine
from .context import Context
from .errors import BuildError


def bin_file(path: Path) -> bytes:
    """A binary file loaded from disk."""
    logger.info(f"Reading binary file {path.name}")
    data = _read_bin_file(path)
    return _build_binfile(data)


def asm_file(path: Path) -> bytes:
    """An ASM file loaded from disk and compiled into binary."""
    logger.info(f"Reading ASM source file {path.name}")
    data = _read_text_file(path)
    return _build_asmfile('\n'.join(data))


def gecko_file(path: Path) -> bytes:
    """A Gecko codelist file loaded from disk and compiled into binary."""
    logger.info(f"Reading Gecko codelist file {path.name}")
    data = _read_text_file(path)
    return _build_geckofile(path, data)


def mgc_file(path: Path) -> list:
    """An MGC file loaded from disk and parsed into a Command list."""
    logger.info(f"Reading MGC file {path.name}")
    data = _read_text_file(path)
    return _build_mgcfile(path, data)


def _read_bin_file(path: Path) -> bytes:
    """Reads a binary file from disk and returns the byte array"""
    try:
        with path.open('rb') as f:
            data = f.read()
    except FileNotFoundError:
        raise BuildError(f"File not found: {str(path)}")
    return data


def _read_text_file(path: Path) -> list[str]:
    """Reads a text file from disk and returns a list of each line of data"""
    try:
        with path.open('r') as f:
            data = f.readlines()
    except FileNotFoundError:
        raise BuildError(f"File not found: {str(path)}")
    except UnicodeDecodeError:
        raise BuildError("Unable to read file; make sure it's a text file")
    return data


def _build_binfile(filedata: bytes) -> bytes:
    """Builds a binary file and returns it in bytes."""
    return filedata


def _build_asmfile(filedata: str) -> bytes:
    """Builds an ASM file and returns it in bytes."""
    compiled_asm = asm.compile_asm(filedata)
    return compiled_asm


def _build_geckofile(path: Path, data: list[str]):
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


def _build_mgcfile(path: Path, data: list[str]) -> list[MGCLine]:
    """Builds an MGC script file and returns it as a list of commands."""
    with Context(path) as c:
        start, end = _preprocess_begin_end(data)
        op_lines = []
        asm_lines = []
        asm_cmd = ''
        asm_args = []
        for line_number, script_line in enumerate(data[start:end], start=start):
            if asm_cmd:
                if not line.is_command(script_line, asm_cmd + 'end'):
                    asm_lines.append(script_line)
                    continue
                asmtext = '\n'.join(asm_lines)
                if asm_cmd == 'c2':
                    asmdata = asm.compile_c2(asmtext, asm_args[0])
                else:
                    asmdata = asm.compile_asm(asmtext)
                asm_args.append(asmdata)
                op_lines.append(MGCLine(c.line_number, asm_cmd, asm_args))
                asm_cmd = ''
                asm_args = []
                asm_lines.clear()
            else:
                c.line_number = line_number
                command, args = line.parse(script_line)
                if not command:
                    continue
                if command in ['asm', 'c2']:
                    asm_cmd = command
                else:
                    op_lines.append(MGCLine(line_number, command, args))
        if asm_cmd:
            raise BuildError("Command does not have an end specified")
        return op_lines


def _preprocess_begin_end(filedata):
    """Finds the !begin and !end lines of the MGC file."""
    start_line = 0
    end_line = len(filedata)
    for line_number, script_line in enumerate(filedata):
        if line.is_command(script_line, 'begin'):
            start_line = line_number+1
            break
    for line_number, script_line in enumerate(reversed(filedata)):
        if line.is_command(script_line, 'end'):
            end_line = len(filedata)-line_number-1
            break
    return start_line, end_line

