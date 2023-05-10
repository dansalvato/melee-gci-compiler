"""compiler.py: Compiles MGC files into a block of data that is ready to write
to the GCI."""
from pathlib import Path
from . import logger
from .commands import src
from .errors import CompileError
from .gci_tools.meleegci import melee_gamedata
from .datatypes import CompilerState


def _init_new_gci() -> melee_gamedata:
    """Creates a new gamedata object from the init_gci MGC script."""
    init_gci_path = Path(__file__).parent/"init_gci"/"init_gci.mgc"
    silent = logger.silent_log
    logger.silent_log = True
    state = src(str(init_gci_path), CompilerState())
    gci_data = bytearray(0x16040)
    for w in state.write_table:
        gci_data[w.address:w.address+len(w.data)] = w.data
    logger.silent_log = silent
    return melee_gamedata(raw_bytes=gci_data)


def _load_gci(gci_path: str, unpacked=False) -> melee_gamedata:
    """Creates a gamedata object by loading an existing GCI file."""
    try:
        input_gci = melee_gamedata(filename=gci_path, packed=not unpacked)
    except FileNotFoundError:
        raise CompileError(f"Input GCI not found: {gci_path}")
    if not unpacked:
        try:
            input_gci.unpack()
        except Exception as e:
            raise CompileError(f"GCI decoder: {e}")
    gci_data = input_gci.raw_bytes
    if len(gci_data) != 0x16040:
        raise CompileError(f"Input GCI is the wrong size; make sure it's a Melee save file")
    return input_gci


def init(root_mgc_path: str=None, input_gci_path: str=None, silent=False, debug=False, nopack=False, unpacked_input=False) -> bytearray:
    """Begins compilation by taking a root MGC path and parameters, then
    returns the raw bytes of the final GCI."""
    logger.silent_log = silent
    logger.debug_log = debug
    if input_gci_path:
        logger.info("Loading and unpacking input GCI")
        input_gci = _load_gci(input_gci_path, unpacked_input)
    else:
        logger.info("Initializing new GCI")
        input_gci = _init_new_gci()
    if root_mgc_path:
        state = src(root_mgc_path, CompilerState())
        for w in state.write_table:
            input_gci.raw_bytes[w.address:w.address+len(w.data)] = w.data
        if state.block_order:
            input_gci.block_order = state.block_order
            input_gci.reorder_blocks()
        for w in state.patch_table:
            input_gci.raw_bytes[w.address:w.address+len(w.data)] = w.data
    input_gci.recompute_checksums()
    if not nopack:
        logger.info("Packing GCI")
        input_gci.pack()
    return input_gci.raw_bytes

