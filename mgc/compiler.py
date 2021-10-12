"""compiler.py: Compiles MGC files into a block of data that is ready to write
to the GCI."""
from pathlib import Path
from . import logger
from . import files
from . import commands
from .errors import CompileError
from .gci_tools.meleegci import melee_gamedata
from .datatypes import CompilerState
from .context import Context
from .context import in_stack


def _init_new_gci() -> melee_gamedata:
    init_gci_path = Path(__file__).parent/"init_gci"/"init_gci.mgc"
    silent = logger.silent_log
    logger.silent_log = True
    state = CompilerState()
    state = commands.src(str(init_gci_path), state.copy())
    gci_data = bytearray(0x16040)
    for entry in state.write_table:
        gci_data[entry.address:entry.address+len(entry.data)] = entry.data
    logger.silent_log = silent
    return melee_gamedata(raw_bytes=gci_data)


def _load_gci(gci_path: str) -> melee_gamedata:
    try:
        input_gci = melee_gamedata(filename=gci_path, packed=True)
    except FileNotFoundError:
        raise CompileError(f"Input GCI not found: {gci_path}")
    try:
        input_gci.unpack()
    except Exception as e:
        raise CompileError(f"GCI decoder: {e}")
    gci_data = input_gci.raw_bytes
    if len(gci_data) != 0x16040:
        raise CompileError(f"Input GCI is the wrong size; make sure it's a Melee save file")
    return input_gci


def compile_file(path: Path, state: CompilerState) -> CompilerState:
    if in_stack(path):
        raise CompileError("MGC files are sourcing each other in an infinite loop")
    with Context(path) as c:
        for line in state.mgc_files[path]:
            c.line_number = line.line_number
            if state.current_macro and line.command.func is not commands.macroend:
                state.macro_files[state.current_macro].append(line)
            else:
                state = line.command(state.copy())
        if state.current_macro:
            raise CompileError("Macro does not have an end")
    return state


def compile_macro(name: str, state: CompilerState) -> CompilerState:
    for line in state.macro_files[name]:
        state = line.command(state.copy())
    return state


def compile(root_mgc_path: str=None, input_gci_path: str=None, silent=False, debug=False, nopack=False) -> bytearray:
    """Main compile routine: Takes a root MGC file path and compiles all data"""
    logger.silent_log = silent
    logger.debug_log = debug
    state = CompilerState()
    if input_gci_path:
        logger.info("Loading and unpacking input GCI")
        input_gci = _load_gci(input_gci_path)
    else:
        logger.info("Initializing new GCI")
        input_gci = _init_new_gci()
    if root_mgc_path:
        state = commands.src(root_mgc_path, state.copy())
    for entry in state.write_table:
        input_gci.raw_bytes[entry.address:entry.address+len(entry.data)] = entry.data
    if state.block_order:
        input_gci.block_order = state.block_order
        input_gci.reorder_blocks()
    for entry in state.patch_table:
        input_gci.raw_bytes[entry.address:entry.address+len(entry.data)] = entry.data
    input_gci.recompute_checksums()
    if not nopack:
        logger.info("Packing GCI")
        input_gci.pack()
    return input_gci.raw_bytes

