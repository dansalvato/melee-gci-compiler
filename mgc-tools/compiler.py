"""compiler.py: Compiles MGC files into a block of data that is ready to write
to the GCI."""
from pathlib import Path
from logger import *
from lineparser import *
from mgc_file import MGCFile
import re

# The earliest location we can inject data into the GCI
GCI_START_OFFSET = 0x2060

# If a GCI file is given to the compiler, this will be replaced with that file
gci_data = bytearray(0x15850)

# The latest !loc pointer
loc_pointer = 0

# This is True if the !gci opcode was used
gci_pointer_mode = False

# Dict that contains each opcode name and the function that handles it
OPCODES = {
    'loc': None,
    'gci': None,
    'src': None,
    'file': None,
    'ascii': None,
    'asm': None,
    'asmend': None,
    'c2': None,
    'c2end': None,
    'geckocodelist': None,
    'begin': None, # Compiler only finds this if defined twice; log warning
    'end': None, # Compiler only finds this if defined twice; log warning
    }

# A dict that contains all loaded MGC filedata, accessible by filename.
# We load all MGC files from disk ahead of time and use this dict to send
# file data to any MGCFile objects we create.
mgc_filedata = {}

# A list of the current MGC file stack if there are nested source files
mgc_stack = []

# The directory of the root MGC file
root_directory = ""

# This gets set to True if the compiler hits an unrecoverable error
stop_compile = False

def load_mgc_file(filepath):
    """Loads a MGC file from disk and stores its data in mgc_filedata"""
    if filepath in mgc_filedata: return [] # Do nothing if the file is already loaded
    filedata = []
    with filepath.open('r') as f:
        filedata = f.readlines()
    # Preprocess file
    filedata = preprocess_mgc_file(filedata)
    # Store file data
    mgc_filedata[filepath] = filedata
    # See if the new file sources any additional files we need to load
    # TODO: Handle binary files and geckocodelist files
    additional_files = []
    for line in filedata:
        op_list = parse_opcodes(line)
        for operation in op_list:
            if operation.codetype != 'COMMAND': continue
            if operation.data.name != 'src': continue
            additional_files.append(Path(root_directory + operation.data.args[0]).absolute())
    return additional_files

def load_all_mgc_files(root_filepath):
    """Loads all required MGC files from disk, starting with the root file"""
    additional_files = load_mgc_file(root_filepath)
    # This shouldn't infinite loop because already-loaded files return None
    for path in additional_files:
        additional_files.append(load_mgc_file(path))

def preprocess_mgc_file(filedata):
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
        script_line = script_line.strip()
        # Consolidate multiple spaces into one space
        script_line = re.sub(r'\s+', ' ', script_line)

        # Look for !begin and !end
        op_list = parse_opcodes(line)
        for operation in op_list:
            if operation.codetype != 'COMMAND': continue
            if operation.data.name == 'begin' and begin_line < 0: begin_line = line_number
            elif operation.data.name == 'end' and end_line < 0: end_line = line_number

    # Wipe everything before !begin and after !end
    if begin_line >= 0 and end_line >= 0:
        if end_line <= begin_line: raise IndexError("!end Command appears before !begin Command")
    if begin_line >= 0:
        for line in filedata[:begin_line+1]: line = '' # !begin gets wiped too
    if end_line >= 0:
        for line in filedata[end_line:]: line = '' # !end gets wiped too

    return filedata
