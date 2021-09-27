"""mgc_file.py: A class that stores the data from an MGC file as a list of
Operations to execute."""
import re
from pathlib import Path
from .pyiiasmh import ppctools
from . import lineparser
from .lineparser import *
from .errors import *
from .logger import log
from collections import namedtuple

MGCLine = namedtuple('MGCLine', ['line_number', 'op_list'])
# This gets changed once compiler.py has a root MGC path
tmp_directory = Path.cwd()

# A dict of macros accessible by name, containing a list of operations
macros = {}

class File:
    def __init__(self, filepath, filedata):
        self.filepath = filepath
        self.filedata = filedata

    def compile_asm_block(self, asm, line_number=None, c2=False, c2_ba=None):
        """Takes an ASM text string and compiles it to hex using pyiiasmh"""
        txtfile = tmp_directory/"code.txt"
        with open(txtfile, 'w') as f:
            f.write(asm)
        try:
            compiled_asm = ppctools.asm_opcodes(tmp_directory)
        except RuntimeError as e:
            if not line_number: line_number = -1
            r = re.search(r'code\.txt\:(\d+)\: Error: (.*?)\\', str(e))
            if r:
                asm_line_number = int(r.group(1))
                error = r.group(2)
                raise CompileError(f"Error compiling ASM: {error}", self, line_number+asm_line_number)
            else:
                raise CompileError(f"Error compiling ASM", self, line_number)
        except Exception as e:
            raise CompileError(f"Error compiling ASM: {e}", self, line_number)
        if c2:
            c2_ba = "%08x" % c2_ba
            try:
                compiled_asm = ppctools.construct_code(compiled_asm, bapo=c2_ba, ctype='C2D2')
            except Exception as e:
                raise CompileError(f"Error compiling ASM: {e}", self, line_number)
        return compiled_asm


class BINFile(File):
    """A file containing binary data"""
    pass

class ASMFile(File):
    """An ASM code file converted to binary data"""
    def __init__(self, filepath, filedata):
        self.filepath = filepath
        self.filedata = bytearray.fromhex(self.compile_asm_block(filedata))

class GeckoCodelistFile(File):
    """A Gecko codelist file converted to binary data"""
    def __init__(self, filepath, filedata):
        self.filepath = filepath
        self.filedata = self.__preprocess(filedata)

    def __preprocess(self, filedata):
        header = bytearray.fromhex('00d0c0de00d0c0de')
        footer = bytearray.fromhex('f000000000000000')
        data = bytearray(0)
        for line_number, line in enumerate(filedata):
            if line[0] != '*': continue
            line = line[1:]
            try:
                data += bytearray.fromhex(line)
            except ValueError:
                raise CompileError("Invalid Gecko code line", self.filepath, line_number)


        return header + data + footer

class MGCFile(File):
    """An MGC script file"""
    def __init__(self, filepath, filedata):
        self.filepath = filepath
        filedata = self.__preprocess(filedata)
        filedata = self.__preprocess_begin_end(filedata)
        op_lines = self.__preprocess_op_lines(filedata)
        op_lines = self.__preprocess_asm(filedata, op_lines)
        op_lines = self.__preprocess_macros(op_lines)
        self.mgc_lines = op_lines

        for line in op_lines:
            line_number = line.line_number
            for op in line.op_list:
                if op.codetype == 'ERROR':
                    raise CompileError(op.data, self, line_number)
                if op.codetype != 'COMMAND': continue
                # TODO: This won't work unless in a preprocess step
                elif op.data.name == 'define':
                    alias_name = '[' + op.data.args[0] + ']'
                    alias_data = op.data.args[1]
                    if alias_name in lineparser.aliases:
                        log('WARNING', f"Alias {alias_name} is already defined and will be overwritten", self, line_number)
                    lineparser.aliases[alias_name] = alias_data

    def get_lines(self):
        return self.mgc_lines

    def __preprocess_op_lines(self, filedata):
        op_lines = []
        open_tag = None
        open_tag_line = 0
        for line_number, line in enumerate(filedata):
            op_list = parse_opcodes(line)
            if not op_list:
                continue
            if open_tag:
                if self._check_close_tag(op_list, open_tag):
                    open_tag = None
                else:
                    continue
            else:
                open_tag = self._check_open_tag(op_list)
                open_tag_line = line_number
            op_lines.append(MGCLine(line_number, op_list))
        if open_tag:
            raise CompileError(f"Command does not have an end specified",
                               self, open_tag_line)
        return op_lines

    def _check_open_tag(self, op_list):
        OPEN_TAG_NAMES = ['asm', 'c2']
        for op in op_list:
            if (op.codetype != 'COMMAND'):
                continue
            if op.data.name in OPEN_TAG_NAMES:
                return op.data.name
        return None

    def _check_close_tag(self, op_list, open_tag):
        for op in op_list:
            if (op.codetype == 'COMMAND' and
                op.data.name == open_tag + 'end'):
                return True
        return False

    def __preprocess_begin_end(self, filedata):
        for line_number, line in enumerate(filedata):
            if line == '!begin':
                for i in range(line_number+1):
                    filedata[i] = ''
                break
        for line_number, line in enumerate(reversed(filedata)):
            if line == '!end':
                line_number = len(filedata)-line_number-1
                filedata = filedata[:line_number]
                break
        return filedata

    def __preprocess(self, filedata):
        """Takes MGC file data loaded from disk and strips everything the compiler
           should ignore, such as comments"""
        multiline_comment = False
        for line_number, line in enumerate(filedata):
            if multiline_comment:
                # If there's no comment ender, wipe the whole line and move on
                comment_index = line.find('*/')
                if comment_index < 0:
                    filedata[line_number] = ''
                    continue
                line = line[comment_index+2:]
            # Trim multi-line comments that start and end on the same line
            line = re.sub(r'\/\*.*?\*\/', '', line)
            # Trim single-line comments
            comment_index = line.find('#')
            if comment_index >= 0: line = line[:comment_index]
            # Trim everything after multi-line comment indicator
            comment_index = line.find('/*')
            if comment_index >= 0:
                line = line[:comment_index]
                multiline_comment = True
            # Trim whitespace
            line = line.strip()
            # Consolidate multiple spaces into one space, unless in quotes
            line = re.sub(r'\s+(?=([^"]*"[^"]*")*[^"]*$)', ' ', line)
            filedata[line_number] = line
        return filedata

    def __preprocess_asm(self, filedata, op_lines):
        ASM_COMMANDS = ['asm', 'c2']
        for index, line in enumerate(op_lines):
            for op in line.op_list:
                if op.codetype != 'COMMAND': continue
                if op.data.name not in ASM_COMMANDS: continue
                c2 = op.data.name == 'c2'
                c2_addr = op.data.args[0] if c2 else None
                start_line = line.line_number + 1
                end_line = op_lines.pop(index+1).line_number
                asm_data = '\n'.join(filedata[start_line:end_line])
                asm_block = self.compile_asm_block(asm_data, line.line_number, c2, c2_addr)
                op_lines[index] = MGCLine(line.line_number, [Operation('HEX', asm_block)])
        return op_lines

    def __preprocess_macros(self, op_lines):
        """Looks for macro definitions and adds them to the macros dict"""
        new_op_lines = []
        mid_macro = False
        macro_start_line = 0
        macro_op_list = []
        for line in op_lines:
            if not mid_macro:
                for op in line.op_list:
                    if op.codetype != 'COMMAND': continue
                    if op.data.name != 'macro': continue
                    macro_name = op.data.args[0]
                    if macro_name in macros:
                        log('WARNING', f"Macro {macro_name} is already defined; overwriting definition", self, line.line_number)
                    mid_macro = True
                    macro_start_line = line.line_number
                    macro_op_list.clear()
                    break
                new_op_lines.append(line)
            else:
                for op in line.op_list:
                    if op.codetype == 'MACRO':
                        raise CompileError("Macros cannot call other macros", self, line.line_number)
                    if op.codetype != 'COMMAND': continue
                    if op.data.name == 'macro':
                        raise CompileError("Macros cannot define other macros", self, line.line_number)
                    if op.data.name != 'macroend': continue
                    mid_macro = False
                    macros[macro_name] = macro_op_list.copy()
                    break
                macro_op_list += line.op_list
        if mid_macro:
            raise CompileError("Macro does not have an end specified", self, macro_start_line)
        return new_op_lines
