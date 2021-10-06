"""Contains custom data classes that are used throughout compilation."""

from copy import copy
from typing import NamedTuple
from pathlib import Path
from dataclasses import dataclass
from dataclasses import field
from .errors import CompileError
from .gci_tools.mem2gci import *
from .context import Context


class WriteEntry(NamedTuple):
    """An entry of data to write to the GCI."""
    address: int
    data: bytes
    context: 'Context'

    def __len__(self):
        return len(self.data)

    def intersects(self, entry: 'WriteEntry') -> bool:
        """Tests if two WriteEntries intersect with each other."""
        return ((self.address <= entry.address and
                 self.address + len(self.data) > entry.address) or
                (entry.address <= self.address and
                 entry.address + len(entry.data) > self.address))


@dataclass
class CompilerState:
    """Keeps track of the current state of the compiler."""
    gci_data: bytearray = bytearray(0x16040)
    loc_pointer: int = 0
    gci_pointer: int = 0
    gci_pointer_mode: bool = False
    patch_mode: bool = False
    mgc_files: dict[Path, list] = field(default_factory=lambda: {})
    bin_files: dict[Path, bytes] = field(default_factory=lambda: {})
    mgc_stack: list[Path] = field(default_factory=lambda: [])
    write_table: list[WriteEntry] = field(default_factory=lambda: [])
    block_order: list[int] = field(default_factory=lambda: [])
    patch_table: list[WriteEntry] = field(default_factory=lambda: [])

    def __call__(self) -> 'CompilerState':
        """Easily creates a shallow copy of this object."""
        return copy(self)


def WriteEntryList(data: bytes, state: CompilerState, context: Context) -> list[WriteEntry]:
    """Creates a list of write entries out of data."""
    if state.gci_pointer_mode:
        if state.gci_pointer < 0:
            raise CompileError("Data pointer must be a positive value", context)
        if state.gci_pointer + len(data) > len(state.gci_data):
            raise CompileError("Attempting to write past the end of the GCI", context)
        return [WriteEntry(state.gci_pointer, data, context)]
    else:
        if state.loc_pointer < 0:
            raise CompileError("Data pointer must be a positive value", context)
        try:
            entries = data2gci(state.loc_pointer, data)
        except ValueError as e:
            raise CompileError(e, context)
        return [WriteEntry(*entry, context) for entry in entries]


class MGCFile(NamedTuple):
    path: Path
