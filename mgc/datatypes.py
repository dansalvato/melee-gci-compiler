"""Contains custom data classes that are used throughout compilation."""

from copy import copy
from pathlib import Path
from dataclasses import dataclass
from dataclasses import field
from .errors import CompileError
from .gci_tools.mem2gci import *
from . import context
from .context import Context
from typing import Callable
from typing import Any


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
CommandArgsType = Callable[[str], Any]


class CompilerState:
    """Keeps track of the current state of the compiler."""
    gci_data: bytearray = bytearray(0x16040)
    loc_pointer: int = 0
    gci_pointer: int = 0
    gci_pointer_mode: bool = False
    patch_mode: bool = False
    asm_open: bool = False
    c2_open: bool = False
    current_macro: str = ''
    mgc_files: dict[Path, list[CommandType]] = field(default_factory=dict)
    bin_files: dict[Path, bytes] = field(default_factory=dict)
    mgc_stack: list[Path] = field(default_factory=list)
    write_table: list[WriteEntry] = field(default_factory=list)
    block_order: list[int] = field(default_factory=list)
    patch_table: list[WriteEntry] = field(default_factory=list)
    macro_files: dict[str, list[CommandType]] = field(default_factory=dict)
    asm_blocks: dict[str, bytes] = field(default_factory=dict)

    def copy(self) -> 'CompilerState':
        """Easily creates a shallow copy of this object."""
        return copy(self)


def WriteEntryList(data: bytes, state: CompilerState) -> list[WriteEntry]:
    """Creates a list of write entries out of data."""
    if state.gci_pointer_mode:
        if state.gci_pointer < 0:
            raise CompileError("Data pointer must be a positive value")
        if state.gci_pointer + len(data) > len(state.gci_data):
            raise CompileError("Attempting to write past the end of the GCI")
        return [WriteEntry(state.gci_pointer, data)]
    else:
        if state.loc_pointer < 0:
            raise CompileError("Data pointer must be a positive value")
        try:
            entries = data2gci(state.loc_pointer, data)
        except ValueError as e:
            raise CompileError(e)
        return [WriteEntry(*entry) for entry in entries]


@dataclass
class MGCFile:
    path: Path
