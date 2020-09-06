"""mgc_file.py: A class that stores the data from an MGC file as a list of
Operations to execute."""
from collections import namedtuple
from lineparser import *
import re

MGCLine = namedtuple('MGCLine', ['line_number', 'op_list'])

class MGCFile:
    def __init__(self, filepath, filedata):
        self.filepath = filepath
        self.filedata = self.__preprocess(filedata)
        self.MGCLines = []

        for line_number, line in enumerate(self.filedata):
            op_list = parse_opcodes(line)
            if op_list:
                self.MGCLines.append(MGCLine(line_number, op_list))



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
                    line = ''
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

        # Wipe everything before !begin and after !end
        # TODO: Make this a better error
        # Errors should show relative path if in root directory, absolute path otherwise
        if begin_line >= 0 and end_line >= 0:
            if end_line <= begin_line: raise IndexError("!end Command appears before !begin Command")
        if begin_line >= 0:
            for line in filedata[:begin_line+1]: line = '' # !begin gets wiped too
        if end_line >= 0:
            for line in filedata[end_line:]: line = '' # !end gets wiped too

        return filedata