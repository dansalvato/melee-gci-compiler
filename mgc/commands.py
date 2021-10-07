from abc import abstractmethod
from typing import Callable
from dataclasses import dataclass
from pathlib import Path
from .datatypes import CompilerState
from .datatypes import WriteEntry, WriteEntryList
from .errors import CompileError
from . import logger
from . import files


def loc(state: CompilerState, address: int) -> CompilerState:
    """Sets the loc pointer."""
    state.gci_pointer_mode = False
    state.patch_mode = False
    state.loc_pointer = address
    return state


def gci(state: CompilerState, address: int) -> CompilerState:
    """Sets the gci pointer."""
    state.gci_pointer_mode = True
    state.patch_mode = False
    state.gci_pointer = address
    return state


def patch(state: CompilerState, address: int) -> CompilerState:
    """Sets the patch pointer."""
    state.gci_pointer_mode = True
    state.patch_mode = True
    state.gci_pointer = address
    return state


def add(state: CompilerState, amount: int) -> CompilerState:
    """Adds to the currently-active pointer."""
    if state.gci_pointer_mode:
        state.gci_pointer += amount
    else:
        state.loc_pointer += amount
    return state


def _write(state: CompilerState, data: bytes) -> CompilerState:
    """(Base class) Writes data to the write table."""
    entries = WriteEntryList(data, state)
    if state.patch_mode:
        state.patch_table += entries
    else:
        _check_collisions(state.write_table, entries)
        state.write_table += entries
    return state


def _check_collisions(old_entries: list[WriteEntry], new_entries: list[WriteEntry]) -> None:
    """Checks for and warns about collisions in the write table."""
    for entry in new_entries:
        for prev_entry in old_entries:
            if entry.intersects(prev_entry):
                logger.warning(f"GCI location 0x{max(prev_entry.address, entry.address):x} "
                                "was already written to by {prev_entry.context.filepath.name} "
                                "(Line {prev_entry.context.line_number+1}) and is being overwritten")
    return


def hex_string(state: CompilerState, data: str) -> CompilerState:
    """Writes a hex string as bytes to the write table."""
    b = bytes.fromhex(data)
    return _write(state, b)


def binary_string(state: CompilerState, data: str) -> CompilerState:
    """Writes a binary string as bytes to the write table."""
    data_hex = format(int(data, 2), 'x')
    if len(data_hex) % 2 > 0:
        data_hex = '0' + data_hex
    b = bytes.fromhex(data_hex)
    return _write(state, b)


def string(state: CompilerState, data: str) -> CompilerState:
    """Writes a string as bytes to the write table."""
    b = bytes(bytes(data, 'utf-8').decode("unicode_escape"), encoding='ascii')
    return _write(state, b)


def fill(state: CompilerState, count: int, pattern: bytes) -> CompilerState:
    """Writes a fill pattern to the write table."""
    b = pattern * count
    return _write(state, b)


def _file(state: CompilerState, path: str, filetype: Callable[[Path], bytes]) -> CompilerState:
    """(Base class) Writes a file to the write table."""
    binpath = Path(path).resolve()
    if not binpath in state.bin_files:
        state.bin_files[binpath] = filetype(binpath)
    data = state.bin_files[binpath]
    return _write(state, data)


def bin(state: CompilerState, path: str) -> CompilerState:
    """Writes a binary file to the write table."""
    return _file(state, path, files.bin_file)


def asmsrc(state: CompilerState, path: str) -> CompilerState:
    """Writes a compiled version of an ASM source file to the write table."""
    return _file(state, path, files.asm_file)


def geckocodelist(state: CompilerState, path: str) -> CompilerState:
    """Writes a Gecko codelist file to the write table."""
    return _file(state, path, files.gecko_file)


def src(state: CompilerState, path: str) -> CompilerState:
    """Sources and compiles an MGC file."""
    filepath = Path(path).resolve()
    if not filepath in state.mgc_files:
        state.mgc_files[filepath] = files.mgc_file(filepath)
        # TODO: Run compile method here
    return state


def asm(state: CompilerState, data: bytes) -> CompilerState:
    """Write a compiled version of an ASM block to the write table."""
    return _write(state, data)


def c2(state: CompilerState, data: bytes) -> CompilerState:
    """Write a compiled version of a C2 ASM block to the write table."""
    return _write(state, data)


def blockorder(state: CompilerState,
               b0: int, b1: int, b2: int, b3: int, b4: int,
               b5: int, b6: int, b7: int, b8: int, b9: int):
    """Changes the order that blocks get arranged in the GCI file."""
    _blockorder = [b0, b1, b2, b3, b4, b5, b6, b7, b8, b9]
    for b in _blockorder:
        if b < 0:
            raise CompileError("Block number cannot be negative")
        elif b > 9:
            raise CompileError("Block number cannot be greater than 9")
    state.block_order = _blockorder
    return state


def echo(state: CompilerState, message: str) -> CompilerState:
    """Logs a message."""
    logger.info(message)
    return state


def asmend(state: CompilerState) -> CompilerState:
    """Not runnable. Signifies the end of an ASM block."""
    message = "!asmend is used without a !asm preceding it"
    raise CompileError(message)
def c2end(state: CompilerState) -> CompilerState:
    """Not runnable. Signifies the end of a C2 ASM block."""
    message = "!c2end is used without a !c2 preceding it"
    raise CompileError(message)
def macroend(state: CompilerState) -> CompilerState:
    """Not runnable. Signifies the end of a macro block."""
    message = "!macroend is used without a !macro preceding it"
    raise CompileError(message)
def begin(state: CompilerState) -> CompilerState:
    """Not runnable. Signifies the beginning of an MGC script."""
    message = "!begin is used more than once in this file"
    raise CompileError(message)
def end(state: CompilerState) -> CompilerState:
    """Not runnable. Signifies the end of an MGC script."""
    message = "!end is used more than once in this file"
    raise CompileError(message)
