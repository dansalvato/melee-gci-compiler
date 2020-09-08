"""mgc_file.py: A class that stores the data from an MGC file as a list of
Operations to execute."""
import re
from .pyiiasmh import ppctools
from . import lineparser
from .lineparser import *
from .errors import *
from .logger import log
from collections import namedtuple

MGCLine = namedtuple('MGCLine', ['line_number', 'op_list'])
tmp_directory = None

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
            compiled_asm = ppctools.construct_code(compiled_asm, bapo=c2_ba, ctype='C2D2')
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
        self.filedata = self.__preprocess(filedata)
        self.filedata, self.asm_blocks = self.__preprocess_asm(filedata)
        self.filedata = self.__preprocess_macros(filedata)
        self.mgc_lines = []

        asm_block_number = 0
        for line_number, line in enumerate(self.filedata):
            op_list = parse_opcodes(line)
            if op_list:
                for index, operation in enumerate(op_list):
                    if operation.codetype == 'ERROR':
                        raise CompileError(operation.data, self, line_number)
                    if operation.codetype != 'COMMAND': continue
                    if operation.data.name == 'asm' or operation.data.name == 'c2':
                        op_list[index].data.args.append(asm_block_number)
                        asm_block_number += 1
                    elif operation.data.name == 'define':
                        alias_name = '[' + operation.data.args[0] + ']'
                        alias_data = operation.data.args[1]
                        if alias_name in lineparser.aliases:
                            log('WARNING', f"Alias {alias_name} is already defined and will be overwritten", self, line_number)
                        lineparser.aliases[alias_name] = alias_data
                self.mgc_lines.append(MGCLine(line_number, op_list))


    def get_lines(self):
        return self.mgc_lines

    def __preprocess(self, filedata):
        """Takes MGC file data loaded from disk and strips everything the compiler
           should ignore, such as comments"""
        multiline_comment = False
        begin_line = -1
        end_line = -1
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
            # Consolidate multiple spaces into one space
            line = re.sub(r'\s+', ' ', line)

            # Look for !begin and !end
            op_list = parse_opcodes(line)
            for operation in op_list:
                if operation.codetype != 'COMMAND': continue
                if operation.data.name == 'begin' and begin_line < 0: begin_line = line_number
                elif operation.data.name == 'end' and end_line < 0: end_line = line_number

            filedata[line_number] = line

        # Wipe everything before !begin and after !end
        if begin_line >= 0 and end_line >= 0:
            if end_line <= begin_line: raise CompileError("!end Command appears before !begin Command", self, end_line)
        if begin_line >= 0:
            for i in range(begin_line+1): filedata[i] = '' # !begin gets wiped too
        if end_line >= 0:
            for i in range(end_line, len(filedata)): filedata[i] = '' # !end gets wiped too
        return filedata

    def __preprocess_asm(self, filedata):
        """Takes the preprocessed MGC file data and compiles the ASM using
           pyiiasmh"""
        asm_blocks = []
        for line_number, line in enumerate(filedata):
            op_list = parse_opcodes(line)
            for operation in op_list:
                if operation.codetype != 'COMMAND': continue
                if operation.data.name == 'asm' or operation.data.name == 'c2':
                    # Send ASM to buffer until asmend/c2end command is reached
                    asm_ended = False
                    asm_buffer = ''
                    for asm_line_number, asm_line in enumerate(filedata[line_number+1:]):
                        asm_op_list = parse_opcodes(asm_line)
                        asm_operation = None
                        if asm_op_list: asm_operation = asm_op_list[0]
                        if asm_operation:
                            if asm_operation.codetype == 'COMMAND':
                                if (operation.data.name == 'asm' and asm_operation.data.name == 'asmend') or \
                                   (operation.data.name == 'c2' and asm_operation.data.name == 'c2end'):
                                   # Compile ASM, store to asm_block
                                   c2 = False
                                   c2_address = None
                                   if operation.data.name == 'c2':
                                    c2 = True
                                    c2_address = operation.data.args[0]
                                   asm_blocks.append(self.compile_asm_block(asm_buffer, line_number, c2, c2_address))
                                   # Wipe end tag, no longer needed
                                   filedata[line_number+asm_line_number+1] = ''
                                   asm_ended = True
                                   break
                        asm_buffer += asm_line + '\n'
                        filedata[line_number+asm_line_number+1] = ''
                    if not asm_ended: raise CompileError(f"!{operation.data.name} Command does not have an end specified", self, line_number)
        return filedata, asm_blocks

    def __preprocess_macros(self, filedata):
        """Looks for macro definitions and adds them to the macros dict"""
        for line_number, line in enumerate(filedata):
            op_list = parse_opcodes(line)
            for operation in op_list:
                if operation.codetype != 'COMMAND': continue
                if operation.data.name != 'macro': continue
                macro_name = operation.data.args[0]
                if macro_name in macros:
                    log('WARNING', f"Macro {macro_name} is already defined; overwriting definition", self, line_number)
                macro_ended = False
                macro_op_list = []
                for macro_line_number, macro_line in enumerate(filedata[line_number+1:]):
                    current_op_list = parse_opcodes(macro_line)
                    macro_operation = None
                    if current_op_list: macro_operation = current_op_list[0]
                    if macro_operation:
                        if macro_operation.codetype == 'COMMAND':
                            if macro_operation.data.name == 'macroend':
                                # Wipe !macroend tag
                               filedata[line_number+macro_line_number+1] = ''
                               macro_ended = True
                               break
                    macro_op_list += current_op_list
                    filedata[line_number+macro_line_number+1] = ''
                if not macro_ended: raise CompileError("Macro does not have an end specified", self, line_number)
                for macro_operation in macro_op_list:
                    if macro_operation.codetype == 'MACRO':
                        raise CompileError("Macros cannot contain other macros", self, line_number)
                macros[macro_name] = macro_op_list
        return filedata