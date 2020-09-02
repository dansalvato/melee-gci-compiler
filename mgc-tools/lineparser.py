"""lineparser.py: Searches text for opcodes and returns appropriate data"""
import string
from collections import namedtuple

CODETYPES = [
    'COMMENT',
    'MULTILINE_COMMENT',
    'MULTILINE_END',
    'BIN',
    'HEX',
    'BEGIN',
    'END',
    'LOC',
    'GCI',
    'SRC',
    'FILE',
    'GECKOCODELIST',
    'STRING',
    'ASM',
    'ASMEND',
    'C2',
    'C2END',
    'ERROR',
    'WARNING',
    'ECHO',
    ]
COMMANDS = [
    'loc',
    'gci',
    'src',
    'file',
    'geckocodelist',
    'string',
    'asm',
    'asmend',
    'c2',
    'c2end',
    'begin',
    'end',
    'echo',
    ]

Operation = namedtuple('Operation', ['codetype', 'data'], defaults=[None, None])

def parse_opcodes(script_line, filepath=None, line_number=0):
    """Parses a script line and returns a list of opcodes and data found.
       This only checks for syntax and doesn't verify the content of the
       data, except hex and binary (which the compiler also does,
       redundantly)."""
    op_list = []
    multiline_comment = None
    # Trim single-line comments
    comment_index = script_line.find('#')
    if comment_index >= 0: script_line = script_line[:comment_index]
    # Trim everything after multi-line comment indicator
    comment_index = script_line.find('/*')
    if comment_index >= 0:
        # If multiline comment ends on the same line, remove the comment only
        end_index = script_line.find('*/')
        if end_index >= 0:
            script_line = script_line[:comment_index] + script_line[end_index + 2:]
        else:
           script_line = script_line[:comment_index]
           multiline_comment = Operation('MULTILINE_COMMENT')
    # Trim whitespace
    script_line = script_line.strip()
    # If the line is empty, we're done
    if script_line == '':
        if multiline_comment: op_list.append(multiline_comment)
        return op_list

    # Check if line is hex
    if script_line[0] in string.hexdigits:
        # Remove all whitespace
        script_line = script_line.translate(dict.fromkeys(map(ord, string.whitespace)))
        try:
            int(script_line, 16)
            op_list.append(Operation('HEX', script_line))
        except ValueError:
            op_list.append(Operation('ERROR', "Invalid syntax"))
    # Check if line is binary
    elif script_line[0] == '%':
        # Remove % character
        script_line = script_line[1:]
        # Remove all whitespace
        script_line = script_line.translate(dict.fromkeys(map(ord, string.whitespace)))
        try:
            int(script_line, 2)
            op_list.append(Operation('BIN', script_line))
        except ValueError:
            op_list.append(Operation('ERROR', "Invalid syntax"))

    if multiline_comment: op_list.append(multiline_comment)
    return op_list
