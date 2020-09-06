"""compiler.py: Compiles MGC files into a block of data that is ready to write
to the GCI."""
from pathlib import Path
from logger import *
from lineparser import *
from mgc_file import MGCFile
from gci_tools.mem2gci import *

# The earliest location we can inject data into the GCI
GCI_START_OFFSET = 0x2060

# The total size of a Melee GCI - this gets replaced by our input GCI file
gci_data = bytearray(0x16040)

# The latest !loc pointer
loc_pointer = 0
gci_pointer = 0

# This is True if the !gci opcode was used
gci_pointer_mode = False

# A dict that contains all loaded MGC filedata, accessible by filename.
# We load all MGC files from disk ahead of time and use this dict to send
# file data to any MGCFile objects we create.
mgc_files = {}

# A list of the current MGC file stack if there are nested source files
mgc_stack = []

# The directory of the root MGC file
root_directory = ""

def compile(root_mgc_path):
    """Main compile routine: Takes a root MGC file path and compiles all data"""
    # Set root directory
    root_mgc_path = Path(root_mgc_path).absolute()
    root_directory = root_mgc_path.parent
    # Load all src files into mgc_files
    _load_all_mgc_files(root_mgc_path)
    # Begin compile
    _compile_file(mgc_files[root_mgc_path])
    with open("temp.gci", 'wb') as f:
        f.write(gci_data)
    return

def _compile_file(mgc_file, ref_mgc_file=None, ref_line_number=None):
    """Compiles the data of a single file; !src makes this function recursive"""
    log('INFO', f"Compiling {mgc_file.filepath.name}", ref_mgc_file, ref_line_number)
    if mgc_file in mgc_stack:
        raise ValueError("MGC files are sourcing each other in an infinite loop")
    mgc_stack.append(mgc_file)
    for line in mgc_file.get_lines():
        for op in line.op_list:
            OPCODE_FUNCS[op.codetype](op.data, mgc_file, line.line_number)
    mgc_stack.pop()

def _load_mgc_file(filepath):
    """Loads a MGC file from disk and stores its data in mgc_files"""
    if filepath in mgc_files: return [] # Do nothing if the file is already loaded
    log('INFO', f"Loading {filepath.name}")
    filedata = []
    parent = filepath.parent
    with filepath.open('r') as f:
        filedata = f.readlines()
    # Store file data
    mgc_files[filepath] = MGCFile(filepath, filedata)
    # See if the new file sources any additional files we need to load
    # TODO: Handle binary files and geckocodelist files
    additional_files = []
    for line in filedata:
        op_list = parse_opcodes(line)
        for operation in op_list:
            if operation.codetype != 'COMMAND': continue
            if operation.data.name != 'src': continue
            additional_files.append(parent.joinpath(operation.data.args[0]))
    return additional_files

def _load_all_mgc_files(root_filepath):
    """Loads all required MGC files from disk, starting with the root file"""
    additional_files = _load_mgc_file(root_filepath)
    # This shouldn't infinite loop because already-loaded files return None
    for path in additional_files:
        additional_files += _load_mgc_file(path)





def _process_bin(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    return
def _process_hex(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    data = bytearray.fromhex(data)
    if gci_pointer_mode:
        if gci_pointer + len(data) > len(gci_data):
            raise IndexError("Attempting to write past the end of the GCI")
        gci_data[gci_pointer:gci_pointer+len(data)] = data
        gci_pointer += len(data)
    return
def _process_command(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    COMMAND_FUNCS[data.name](data.args, mgc_file, line_number)
    return
def _process_warning(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    return
def _process_error(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    log('ERROR', data, mgc_file, line_number)
    return



def _cmd_process_loc(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    gci_pointer_mode = False
    loc_pointer = data[0]
    return
def _cmd_process_gci(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    gci_pointer_mode = True
    gci_pointer = data[0]
    return
def _cmd_process_add(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    if gci_pointer_mode: gci_pointer += data[0]
    else: loc_pointer += data[0]
    return
def _cmd_process_src(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    file = mgc_file.filepath.parent.joinpath(data[0])
    _compile_file(mgc_files[file], mgc_file, line_number)
    return
def _cmd_process_file(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    return
def _cmd_process_geckocodelist(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    return
def _cmd_process_string(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    return
def _cmd_process_asm(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    asm_block_num = int(data[0])
    _process_hex(mgc_file.asm_blocks[asm_block_num], mgc_file, line_number)
    return
def _cmd_process_asmend(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    return
def _cmd_process_c2(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    return
def _cmd_process_c2end(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    return
def _cmd_process_begin(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    log('WARNING', "!begin is used more than once; ignoring this one", mgc_file, line_number)
    return
def _cmd_process_end(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    log('WARNING', "!end is used more than once; ignoring this one", mgc_file, line_number)
    return
def _cmd_process_echo(data, mgc_file, line_number):
    global gci_data, loc_pointer, gci_pointer, gci_pointer_mode
    return



OPCODE_FUNCS = {
    'BIN': _process_bin,
    'HEX': _process_hex,
    'COMMAND': _process_command,
    'WARNING': _process_warning,
    'ERROR': _process_error,
}

COMMAND_FUNCS = {
    'loc': _cmd_process_loc,
    'gci': _cmd_process_gci,
    'add': _cmd_process_add,
    'src': _cmd_process_src,
    'file': _cmd_process_file,
    'geckocodelist': _cmd_process_geckocodelist,
    'string': _cmd_process_string,
    'asm': _cmd_process_asm,
    'asmend': _cmd_process_asmend,
    'c2': _cmd_process_c2,
    'c2end': _cmd_process_c2end,
    'begin': _cmd_process_begin,
    'end': _cmd_process_end,
    'echo': _cmd_process_echo,
}