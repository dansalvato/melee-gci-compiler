"""compiler.py: Compiles MGC files into a block of data that is ready to write
to the GCI."""
from pathlib import Path
from . import logger, builder
from .logger import log
from .errors import CompileError
from .gci_tools.mem2gci import *
from .gci_tools.meleegci import melee_gamedata

# The earliest location we can inject data into the GCI
GCI_START_OFFSET = 0x2060

# The total size of a Melee GCI - this gets replaced by our input GCI file
gci_data = bytearray(0x16040)

# The latest !loc and !gci pointers
loc_pointer = 0
gci_pointer = 0
gci_pointer_mode = False
patch_mode = False

# A dict that contains all loaded MGC filedata, accessible by filename.
# We load all MGC files from disk ahead of time and use this dict to send file
# data to any MGCFile objects we create.
mgc_files = {}
bin_files = {}
geckocodelist_files = {}

# A list of the current MGC file stack if there are nested source files
mgc_stack = []

# A list of (address, length) tuples used to see if writing to the same address
# more than once
write_history = []

# If !blockorder is used, the new block order goes here
block_order = []

# A list of (address, bytearray) tuples for writing !patch data at the end
patch_table = []

def _init_new_gci() -> None:
    init_gci_path = Path(__file__).parent/"init_gci"/"init_gci.mgc"
    silent = logger.silent_log
    logger.silent_log = True
    _load_all_mgc_files(init_gci_path)
    _compile_file(init_gci_path)
    logger.silent_log = silent

def compile(root_mgc_path: str=None, input_gci_path: str=None, silent=False, debug=False, nopack=False):
    """Main compile routine: Takes a root MGC file path and compiles all data"""
    global write_history, gci_data, block_order
    logger.silent_log = silent
    logger.debug_log = debug
    # Set root directory
    root_path = Path(root_mgc_path).absolute() if root_mgc_path else None
    if root_path:
        builder.tmp_directory = root_path.parent/"tmp"
        try:
            builder.tmp_directory.mkdir(exist_ok=True)
        except FileNotFoundError:
            raise CompileError("Unable to create tmp directory")

    if input_gci_path:
        log('INFO', "Loading and unpacking input GCI")
        try:
            input_gci = melee_gamedata(filename=input_gci_path, packed=True)
        except FileNotFoundError:
            raise CompileError(f"Input GCI not found: {input_gci_path}")
        try:
            input_gci.unpack()
        except Exception as e:
            raise CompileError(f"GCI decoder: {e}")
        gci_data = input_gci.raw_bytes
        if len(gci_data) != 0x16040:
            raise CompileError(f"Input GCI is the wrong size; make sure it's a Melee save file")
    else:
        input_gci = None
        log('INFO', "Initializing new GCI")
        _init_new_gci()
    write_history = []
    if root_path:
        # Load all src files into mgc_files
        _load_all_mgc_files(root_path)
        # Begin compile
        _compile_file(root_path)

    if input_gci:
        input_gci.raw_bytes = gci_data
    else:
        input_gci = melee_gamedata(raw_bytes=gci_data)
    if block_order:
        input_gci.block_order = block_order
        input_gci.reorder_blocks()
    # Done with everything except packing, write the patch table
    for address, data in patch_table:
        input_gci.raw_bytes[address:address+len(data)] = data
    input_gci.recompute_checksums()
    if not nopack:
        log('INFO', "Packing GCI")
        input_gci.pack()
    return input_gci.raw_bytes

def _compile_file(filepath, ref_line_number=None):
    """Compiles the data of a single file; !src makes this function recursive"""
    mgc_file = mgc_files[filepath]
    log('INFO', f"Compiling {filepath.name}", ref_line_number)
    if mgc_file in mgc_stack:
        raise CompileError("MGC files are sourcing each other in an infinite loop", ref_line_number)
    mgc_stack.append(mgc_file)
    logger.push_file(filepath)
    for line in mgc_file:
        for op in line.op_list:
            OPCODE_FUNCS[op.codetype](op.data, filepath, line.line_number)
    logger.pop_file()
    mgc_stack.pop()

def _load_mgc_file(filepath):
    """Loads a MGC file from disk and stores its data in mgc_files"""
    filepath = filepath.resolve()
    if filepath in mgc_files: return [] # Do nothing if the file is already loaded
    log('INFO', f"Loading MGC file {filepath.name}")
    filedata = []
    parent = filepath.parent
    filedata = _read_text_file(filepath)
    # Store file data
    logger.push_file(filepath)
    newfile = builder.build_mgcfile(filedata)
    logger.pop_file()
    mgc_files[filepath] = newfile
    # See if the new file sources any additional files we need to load
    additional_files = []
    for line in newfile:
        for op in line.op_list:
            if op.codetype != 'COMMAND': continue
            if op.data.name == 'src':
                additional_files.append(parent.joinpath(op.data.args[0]))
            elif op.data.name == 'asmsrc':
                _load_asm_file(parent.joinpath(op.data.args[0]))
            elif op.data.name == 'geckocodelist':
                _load_geckocodelist_file(parent.joinpath(op.data.args[0]))
            elif op.data.name == 'file':
                _load_bin_file(parent.joinpath(op.data.args[0]))
    return additional_files

def _read_text_file(filepath):
    """Reads a text file from disk and returns a list of each line of data"""
    try:
        with filepath.open('r') as f:
            filedata = f.readlines()
    except FileNotFoundError:
        raise CompileError(f"File not found: {str(filepath)}")
    except UnicodeDecodeError:
        raise CompileError("Unable to read file; make sure it's a text file")
    return filedata

def _read_bin_file(filepath):
    """Reads a binary file from disk and returns the byte array"""
    try:
        with filepath.open('rb') as f:
            filedata = f.read()
    except FileNotFoundError:
        raise CompileError(f"File not found: {str(filepath)}")
    return filedata

def _load_geckocodelist_file(filepath):
    """Loads a Gecko codelist file from disk and stores its data in
       geckocodelist_files"""
    filepath = filepath.resolve()
    if filepath in bin_files: return
    log('INFO', f"Loading Gecko codelist file {filepath.name}")
    filedata = _read_text_file(filepath)
    logger.push_file(filepath)
    bin_files[filepath] = builder.build_geckofile(filedata)
    logger.pop_file()

def _load_bin_file(filepath):
    """Loads a binary file from disk and stores its data in bin_files"""
    filepath = filepath.resolve()
    if filepath in bin_files: return
    log('INFO', f"Loading binary file {filepath.name}")
    filedata = _read_bin_file(filepath)
    logger.push_file(filepath)
    bin_files[filepath] = builder.build_binfile(filedata)
    logger.pop_file()

def _load_asm_file(filepath):
    """Loads an ASM code file from disk and stores its data in bin_files
       (it gets compiled to binary as we load it from disk)"""
    filepath = filepath.resolve()
    if filepath in bin_files: return
    log('INFO', f"Loading ASM source file {filepath.name}")
    filedata = _read_text_file(filepath)
    logger.push_file(filepath)
    bin_files[filepath] = builder.build_asmfile(filedata)
    logger.pop_file()

def _load_all_mgc_files(root_filepath):
    """Loads all required MGC files from disk, starting with the root file"""
    additional_files = _load_mgc_file(root_filepath)
    # This shouldn't infinite loop because already-loaded files return None
    for path in additional_files:
        additional_files += _load_mgc_file(path)



def _write_data(data: bytearray, filepath: Path, line_number: int) -> None:
    """Writes a byte array to the GCI"""
    global gci_data, loc_pointer, gci_pointer, write_history, block_order, patch_table
    if gci_pointer_mode:
        if gci_pointer < 0:
            raise CompileError("Data pointer must be a positive value", line_number)
        if not patch_mode:
            log('DEBUG', f"Writing 0x{len(data):x} bytes in gci mode:", line_number)
        if gci_pointer + len(data) > len(gci_data):
            raise CompileError("Attempting to write past the end of the GCI", line_number)
        if patch_mode:
            log('DEBUG', f"Sending entry to patch table for location 0x{gci_pointer:x}", line_number)
            patch_table.append((gci_pointer, data))
            gci_pointer += len(data)
            return
        write_table = [(gci_pointer, len(data))]
        gci_pointer += len(data)
    else:
        if loc_pointer < 0:
            raise CompileError("Data pointer must be a positive value", line_number)
        log('DEBUG', f"Writing 0x{len(data):x} bytes in loc mode:", line_number)
        try:
            write_table = data2gci(loc_pointer, len(data))
        except ValueError as e:
            raise CompileError(e, line_number)
        loc_pointer += len(data)
    data_pointer = 0
    _check_write_history(write_table, filepath, line_number)
    for entry in write_table:
        pointer, data_length = entry
        log('DEBUG', f"        0x{data_length:x} bytes to 0x{pointer:x}", line_number)
        gci_data[pointer:pointer+data_length] = data[data_pointer:data_pointer+data_length]
        data_pointer += data_length
    write_history.append((write_table, filepath, line_number))
    return

def _check_write_history(write_table, filepath, line_number):
    for entry in write_table:
        gci_pointer, data_length = entry
        for history_entry in write_history:
            history_write_table = history_entry[0]
            history_filepath = history_entry[1]
            history_line_number = history_entry[2]
            for history_write_table_entry in history_write_table:
                history_pointer, history_length = history_write_table_entry
                if (history_pointer <= gci_pointer and history_pointer + history_length > gci_pointer) or \
                   (gci_pointer <= history_pointer and gci_pointer + data_length > history_pointer):
                    log('WARNING', f"GCI location 0x{max(history_pointer, gci_pointer):x} was already written to by {history_filepath.name} (Line {history_line_number+1}) and is being overwritten", line_number)
                    return

def _process_bin(data, filepath, line_number):
    data_hex = format(int(data, 2), 'x')
    if len(data_hex) % 2 > 0:
        data_hex = '0' + data_hex
    _process_hex(data_hex, filepath, line_number)
    return
def _process_hex(data, filepath, line_number):
    data = bytearray.fromhex(data)
    _write_data(data, filepath, line_number)
    return
def _process_command(data, filepath, line_number):
    COMMAND_FUNCS[data.name](data.args, filepath, line_number)
    return
def _process_warning(data, filepath, line_number):
    log('WARNING', data, line_number)
    return
def _process_error(data, filepath, line_number):
    raise CompileError(data, line_number)
def _process_macro(data, filepath, line_number):
    macro_name = data.name
    macro_count = data.count
    if not macro_name in builder.macros:
        raise CompileError(f"Undefined macro: {macro_name}", line_number)
    op_list = builder.macros[macro_name]
    for _ in range(macro_count):
        for op in op_list:
            OPCODE_FUNCS[op.codetype](op.data, filepath, line_number)


def _cmd_process_loc(data, filepath, line_number):
    global loc_pointer, gci_pointer, gci_pointer_mode, patch_mode
    gci_pointer_mode = False
    patch_mode = False
    loc_pointer = data[0]
    return
def _cmd_process_gci(data, filepath, line_number):
    global loc_pointer, gci_pointer, gci_pointer_mode, patch_mode
    gci_pointer_mode = True
    patch_mode = False
    gci_pointer = data[0]
    return
def _cmd_process_patch(data, filepath, line_number):
    global loc_pointer, gci_pointer, gci_pointer_mode, patch_mode
    gci_pointer_mode = True
    patch_mode = True
    gci_pointer = data[0]
    return
def _cmd_process_add(data, filepath, line_number):
    global loc_pointer, gci_pointer, gci_pointer_mode
    if gci_pointer_mode: gci_pointer += data[0]
    else: loc_pointer += data[0]
    return
def _cmd_process_src(data, filepath, line_number):
    file = filepath.parent.joinpath(data[0]).resolve()
    _compile_file(file, line_number)
    return
def _cmd_process_asmsrc(data, filepath, line_number):
    _cmd_process_file(data, filepath, line_number)
    return
def _cmd_process_file(data, filepath, line_number):
    file = filepath.parent.joinpath(data[0]).resolve()
    _write_data(bin_files[file], filepath, line_number)
    return
def _cmd_process_geckocodelist(data, filepath, line_number):
    file = filepath.parent.joinpath(data[0]).resolve()
    _write_data(bin_files[file], filepath, line_number)
    return
def _cmd_process_string(data, filepath, line_number):
    _write_data(bytearray(bytes(data[0], 'utf-8').decode("unicode_escape"), encoding='ascii'), filepath, line_number)
    return
def _cmd_process_fill(data, filepath, line_number):
    _process_hex(data[1] * data[0], filepath, line_number)
    return
def _cmd_process_asm(data, filepath, line_number):
    # ASM blocks are currently turned into hex write ops in builder.py
    return
def _cmd_process_asmend(data, filepath, line_number):
    raise CompileError("!asmend is used without a !asm preceding it", line_number)
def _cmd_process_c2(data, filepath, line_number):
    # ASM blocks are currently turned into hex write ops in builder.py
    return
def _cmd_process_c2end(data, filepath, line_number):
    raise CompileError("!c2end is used without a !c2 preceding it", line_number)
def _cmd_process_macro(data, filepath, line_number):
    return
def _cmd_process_macroend(data, filepath, line_number):
    raise CompileError("!macroend is used without a !macro preceding it", line_number)
def _cmd_process_define(data, filepath, line_number):
    # Aliases are added to the dict in MGCFile's init while the script is being
    # parsed into Operations
    return
def _cmd_process_begin(data, filepath, line_number):
    log('WARNING', "!begin is used more than once; ignoring this one", line_number)
    return
def _cmd_process_end(data, filepath, line_number):
    log('WARNING', "!end is used more than once; ignoring this one", line_number)
    return
def _cmd_process_echo(data, filepath, line_number):
    log('INFO', data[0])
    return
def _cmd_process_blockorder(data, filepath, line_number):
    global block_order
    for arg in data:
        if arg < 0: raise CompileError("Block number cannot be negative", line_number)
        elif arg > 9: raise CompileError("Block number cannot be greater than 9", line_number)
    block_order = data
    return



OPCODE_FUNCS = {
    'BIN': _process_bin,
    'HEX': _process_hex,
    'COMMAND': _process_command,
    'MACRO': _process_macro,
    'WARNING': _process_warning,
    'ERROR': _process_error,
}

COMMAND_FUNCS = {
    'loc': _cmd_process_loc,
    'gci': _cmd_process_gci,
    'patch': _cmd_process_patch,
    'add': _cmd_process_add,
    'src': _cmd_process_src,
    'asmsrc': _cmd_process_asmsrc,
    'file': _cmd_process_file,
    'geckocodelist': _cmd_process_geckocodelist,
    'string': _cmd_process_string,
    'fill': _cmd_process_fill,
    'asm': _cmd_process_asm,
    'asmend': _cmd_process_asmend,
    'c2': _cmd_process_c2,
    'c2end': _cmd_process_c2end,
    'macro': _cmd_process_macro,
    'macroend': _cmd_process_macroend,
    'define': _cmd_process_define,
    'begin': _cmd_process_begin,
    'end': _cmd_process_end,
    'echo': _cmd_process_echo,
    'blockorder': _cmd_process_blockorder,
}
