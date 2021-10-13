"""commands.py: Commands that were parsed from an MGC script file. These
commands take the current compiler state and modify or add data to it."""
from typing import Callable
from pathlib import Path
from . import logger
from .files import asm_file, bin_file, gecko_file, mgc_file
from .datatypes import CompilerState
from .datatypes import WriteEntry, WriteEntryList
from .errors import CompileError
from .context import Context
from .context import in_stack


def loc(address: int, state: CompilerState) -> CompilerState:
    """Sets the loc pointer."""
    state.gci_pointer_mode = False
    state.patch_mode = False
    state.pointer = address
    return state


def gci(address: int, state: CompilerState) -> CompilerState:
    """Sets the gci pointer."""
    state.gci_pointer_mode = True
    state.patch_mode = False
    state.pointer = address
    return state


def patch(address: int, state: CompilerState) -> CompilerState:
    """Sets the patch pointer."""
    state.gci_pointer_mode = True
    state.patch_mode = True
    state.pointer = address
    return state


def add(amount: int, state: CompilerState) -> CompilerState:
    """Adds to the currently-active pointer."""
    state.pointer += amount
    return state


def write(data: bytes, state: CompilerState) -> CompilerState:
    """(Base class) Writes data to the write table."""
    entries = WriteEntryList(data, state)
    if state.patch_mode:
        state.patch_table += entries
    else:
        _check_collisions(state.write_table, entries)
        state.write_table += entries
    state.pointer += sum([len(entry.data) for entry in entries])
    return state


def _check_collisions(old_entries: list[WriteEntry], new_entries: list[WriteEntry]) -> None:
    """Checks for and warns about collisions in the write table."""
    for entry in new_entries:
        for prev_entry in old_entries:
            if entry.intersects(prev_entry):
                logger.warning(f"GCI location 0x{max(prev_entry.address, entry.address):x} "
                               f"was already written to by {prev_entry.context.path.name} "
                               f"(Line {prev_entry.context.line_number+1}) and is being overwritten")
    return


def string(data: str, state: CompilerState) -> CompilerState:
    """Writes a string as bytes to the write table. Escape characters are decoded."""
    b = bytes(bytes(data, 'utf-8').decode("unicode_escape"), encoding='ascii')
    return write(b, state)


def fill(count: int, pattern: bytes, state: CompilerState) -> CompilerState:
    """Writes a fill pattern to the write table."""
    b = pattern * count
    return write(b, state)


def _file(path: str, filetype: Callable[[Path], bytes], state: CompilerState) -> CompilerState:
    """(Base class) Writes a file to the write table."""
    binpath = (state.path/Path(path)).resolve()
    if not binpath in state.bin_files:
        state.bin_files[binpath] = filetype(binpath)
    data = state.bin_files[binpath]
    return write(data, state)


def bin(path: str, state: CompilerState) -> CompilerState:
    """Writes a binary file to the write table."""
    return _file(path, bin_file, state)


def asmsrc(path: str, state: CompilerState) -> CompilerState:
    """Writes a compiled version of an ASM source file to the write table."""
    return _file(path, asm_file, state)


def geckocodelist(path: str, state: CompilerState) -> CompilerState:
    """Writes a Gecko codelist file to the write table."""
    return _file(path, gecko_file, state)


def src(path: str, state: CompilerState) -> CompilerState:
    """Sources and compiles an MGC file."""
    oldpath = state.path
    filepath = (state.path/Path(path)).resolve()
    if not filepath in state.mgc_files:
        state.mgc_files[filepath] = mgc_file(filepath)
    state.path = filepath.parent
    state = _compile_file(filepath, state)
    state.path = oldpath
    return state


def _compile_file(path: Path, state: CompilerState) -> CompilerState:
    """Compiles an MGC file requested by the !src command."""
    if in_stack(path):
        raise CompileError("MGC files are sourcing each other in an infinite loop")
    with Context(path) as c:
        for line in state.mgc_files[path]:
            c.line_number = line.line_number
            func = _FUNCS[line.command]
            if state.current_macro and func is not macroend:
                state.macro_files[state.current_macro].append(line)
            else:
                state = func(*line.args, state.copy())
        if state.current_macro:
            raise CompileError("Macro does not have an end")
    return state


def asm(data: bytes, state: CompilerState) -> CompilerState:
    """Writes a compiled version of an ASM block to the write table."""
    return write(data, state)


def c2(data: bytes, state: CompilerState) -> CompilerState:
    """Writes a compiled version of a C2 ASM block to the write table."""
    return write(data, state)


def macro(name: str, state: CompilerState) -> CompilerState:
    """Defines a macro and adds all following commands to it until the end tag."""
    if state.current_macro:
        raise CompileError("Cannot define a macro inside another macro")
    state.current_macro = name
    if name in state.macro_files:
        logger.warning(f"Macro {name} already exists and is being overwritten")
    state.macro_files[name] = []
    return state


def callmacro(name: str, count: int, state: CompilerState) -> CompilerState:
    """Calls and runs a macro that was defined earlier."""
    if state.current_macro:
        raise CompileError("Cannot call a macro from within another macro""")
    if not state.macro_files[name]:
        raise CompileError(f"Macro {name} is undefined")
    for _ in range(count):
        for line in state.macro_files[name]:
            func = _FUNCS[line.command]
            state = func(*line.args, state.copy())
    return state


def blockorder(b0: int, b1: int, b2: int, b3: int, b4: int,
               b5: int, b6: int, b7: int, b8: int, b9: int,
               state: CompilerState) -> CompilerState:
    """Changes the order that blocks get arranged in the GCI file."""
    block_order = [b0, b1, b2, b3, b4, b5, b6, b7, b8, b9]
    for b in block_order:
        if b < 0:
            raise CompileError("Block number cannot be negative")
        elif b > 9:
            raise CompileError("Block number cannot be greater than 9")
    state.block_order = block_order
    return state


def echo(message: str, state: CompilerState) -> CompilerState:
    """Logs a message."""
    logger.info(message)
    return state


def macroend(state: CompilerState) -> CompilerState:
    """Ends a macro block or raises an error if orphaned."""
    if state.current_macro:
        state.current_macro = ''
        return state
    message = "!macroend is used without a !macro preceding it"
    raise CompileError(message)


def asmend(_: CompilerState) -> CompilerState:
    """Not runnable. Signifies the end of an ASM block."""
    message = "!asmend is used without a !asm preceding it"
    raise CompileError(message)


def c2end(_: CompilerState) -> CompilerState:
    """Not runnable. Signifies the end of a C2 ASM block."""
    message = "!c2end is used without a !c2 preceding it"
    raise CompileError(message)


def begin(_: CompilerState) -> CompilerState:
    """Not runnable. Signifies the beginning of an MGC script."""
    message = "!begin is used more than once in this file"
    raise CompileError(message)


def end(_: CompilerState) -> CompilerState:
    """Not runnable. Signifies the end of an MGC script."""
    message = "!end is used more than once in this file"
    raise CompileError(message)


def define(_: CompilerState) -> CompilerState:
    """Unreachable, because aliases are handled in preprocessing."""
    message = "Preprocessor failed to handle !define"
    raise CompileError(message)


_FUNCS: dict[str, Callable] = {
    'loc': loc,
    'gci': gci,
    'patch': patch,
    'add': add,
    'write': write,
    'src': src,
    'asmsrc': asmsrc,
    'file': bin,
    'bin': bin,
    'geckocodelist': geckocodelist,
    'string': string,
    'fill': fill,
    'asm': asm,
    'asmend': asmend,
    'c2': c2,
    'c2end': c2end,
    'begin': begin,
    'end': end,
    'echo': echo,
    'macro': macro,
    'macroend': macroend,
    'callmacro': callmacro,
    'blockorder': blockorder,
    'define': define
    }

