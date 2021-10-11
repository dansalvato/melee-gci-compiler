"""Contains custom data classes that are used throughout compilation."""

from copy import copy
from pathlib import Path
from dataclasses import dataclass
from dataclasses import field
from .errors import CompileError
from .gci_tools.mem2gci import *
from . import logger
from . import context
from .context import Context
from typing import NamedTuple
from typing import Callable


@dataclass
class WriteEntry:
    """An entry of data to write to the GCI."""
    address: int
    data: bytes
    context: Context = field(default_factory=context.top, init=False)

    def __len__(self):
        return len(self.data)

    def intersects(self, entry: 'WriteEntry') -> bool:
        """Tests if two WriteEntries intersect with each other."""
        return ((self.address <= entry.address and
                 self.address + len(self.data) > entry.address) or
                (entry.address <= self.address and
                 entry.address + len(entry.data) > self.address))


# Type aliases
CommandType = Callable[..., 'CompilerState']


class MGCLine(NamedTuple):
    """A parsed MGC script line, containing the line number from its original
    file (for logging) and a command. The command already has all its args
    in place; it only needs a CompilerState as a parameter when called."""
    line_number: int
    command: CommandType


class CompilerState:
    """Keeps track of the current state of the compiler."""
    path: Path = Path()
    gci_data: bytearray = bytearray(0x16040)
    pointer: int = 0
    gci_pointer_mode: bool = False
    patch_mode: bool = False
    current_macro: str = ''
    mgc_files: dict[Path, list[MGCLine]] = {}
    bin_files: dict[Path, bytes] = {}
    macro_files: dict[str, list[MGCLine]] = {}
    asm_blocks: dict[str, bytes] = {}
    write_table: list[WriteEntry] = []
    patch_table: list[WriteEntry] = []
    block_order: list[int] = []

    def copy(self) -> 'CompilerState':
        """Easily creates a shallow copy of this object."""
        return copy(self)


def WriteEntryList(data: bytes, state: CompilerState) -> list[WriteEntry]:
    """Creates a list of write entries out of data."""
    if state.gci_pointer_mode:
        logger.debug(f"Writing 0x{len(data):x} bytes in gci mode:")
        if state.pointer < 0:
            raise CompileError("Data pointer must be a positive value")
        if state.pointer + len(data) > len(state.gci_data):
            raise CompileError("Attempting to write past the end of the GCI")
        logger.debug(f"        0x{len(data):x} bytes to 0x{state.pointer:x}")
        return [WriteEntry(state.pointer, data)]
    else:
        logger.debug(f"Writing 0x{len(data):x} bytes in loc mode:")
        if state.pointer < 0:
            raise CompileError("Data pointer must be a positive value")
        try:
            entries = data2gci(state.pointer, data)
        except ValueError as e:
            raise CompileError(e)
        for pointer, data in entries:
            logger.debug(f"        0x{len(data):x} bytes to 0x{pointer:x}")
        return [WriteEntry(*entry) for entry in entries]

