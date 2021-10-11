"""builder.py: A class that stores the data from an MGC file as a list of
Operations to execute."""
from pathlib import Path
from collections import namedtuple
from . import lineparser
from . import logger
from .context import Context
from .errors import *
from . import asm

MGCLine = namedtuple('MGCLine', ['line_number', 'op_list'])
# This gets changed once compiler.py has a root MGC path
tmp_directory = Path('')
current_path = Path('')
# A dict of macros accessible by name, containing a list of operations
macros = {}

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

def build_mgcfile(filedata):
    start_line, end_line = _preprocess_begin_end(filedata)
    op_lines = _preprocess_op_lines(filedata, start_line, end_line)
    op_lines = _preprocess_asm(filedata, op_lines)
    op_lines = _preprocess_macros(op_lines)
    # TODO: Raise errors in lineparser.py and try/catch here
    for line in op_lines:
        line_number = line.line_number
        for op in line.op_list:
            if op.codetype == 'ERROR':
                raise CompileError(op.data, line_number)
    return op_lines

def _preprocess_op_lines(filedata, start_line, end_line):
    op_lines = []
    open_tag = None
    open_tag_line = 0
    for line_number, line in enumerate(filedata[start_line:end_line], start=start_line):
        op_list = lineparser.parse_opcodes(line)
        if not op_list:
            continue
        _add_defines(op_list, line_number)
        if open_tag:
            if _check_close_tag(op_list, open_tag):
                open_tag = None
            else:
                continue
        else:
            open_tag = _check_open_tag(op_list)
            open_tag_line = line_number
        op_lines.append(MGCLine(line_number, op_list))
    if open_tag:
        raise CompileError(f"Command does not have an end specified",
                           open_tag_line)
    return op_lines

def _add_defines(op_list, line_number):
    for op in _get_commands(op_list):
        if op.data.name != 'define': continue
        alias_name = '[' + op.data.args[0] + ']'
        alias_data = op.data.args[1]
        if alias_name in lineparser.aliases:
            logger.warning(f"Alias {alias_name} is already defined and will be overwritten", line_number)
        lineparser.aliases[alias_name] = alias_data
    return

def _check_open_tag(op_list):
    OPEN_TAG_NAMES = ['asm', 'c2']
    for op in _get_commands(op_list):
        if op.data.name in OPEN_TAG_NAMES:
            return op.data.name
    return None

def _check_close_tag(op_list, open_tag):
    for op in _get_commands(op_list):
        if op.data.name == open_tag + 'end':
            return True
    return False

def _get_commands(op_list):
    return [op for op in op_list if op.codetype == 'COMMAND']

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

def _preprocess_asm(filedata, op_lines):
    ASM_COMMANDS = ['asm', 'c2']
    for index, line in enumerate(op_lines):
        for op in _get_commands(line.op_list):
            if op.data.name not in ASM_COMMANDS: continue
            c2 = op.data.name == 'c2'
            start_line = line.line_number + 1
            end_line = op_lines.pop(index+1).line_number
            asm_data = ''.join(filedata[start_line:end_line])
            if c2:
                c2_addr = op.data.args[0]
                asm_block = asm.compile_c2(asm_data, c2_addr)
            else:
                asm_block = asm.compile_asm(asm_data)
            op_lines[index] = MGCLine(line.line_number, [lineparser.Operation('HEX', asm_block)])
    return op_lines

def _preprocess_macros(op_lines):
    """Looks for macro definitions and adds them to the macros dict"""
    new_op_lines = []
    mid_macro = False
    macro_start_line = 0
    macro_op_list = []
    for line in op_lines:
        if not mid_macro:
            for op in _get_commands(line.op_list):
                if op.data.name != 'macro': continue
                macro_name = op.data.args[0]
                if macro_name in macros:
                    logger.warning(f"Macro {macro_name} is already defined; overwriting definition", line.line_number)
                mid_macro = True
                macro_start_line = line.line_number
                macro_op_list.clear()
                break
            new_op_lines.append(line)
        else:
            for op in line.op_list:
                if op.codetype == 'MACRO':
                    raise CompileError("Macros cannot call other macros", line.line_number)
                if op.codetype != 'COMMAND': continue
                if op.data.name == 'macro':
                    raise CompileError("Macros cannot define other macros", line.line_number)
                if op.data.name != 'macroend': continue
                mid_macro = False
                macros[macro_name] = macro_op_list.copy()
                break
            macro_op_list += line.op_list
    if mid_macro:
        raise CompileError("Macro does not have an end specified", macro_start_line)
    return new_op_lines
