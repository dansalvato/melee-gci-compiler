from abc import abstractmethod
from typing import Protocol
from typing import Callable
from dataclasses import dataclass
from pathlib import Path
from .datatypes import CompilerState
from .datatypes import WriteEntry, WriteEntryList
from .datatypes import Context, EMPTY_CONTEXT
from . import logger
from . import files


class Command(Protocol):
    """Basic representation of an MGC command operation."""

    @abstractmethod
    def run(self, state: CompilerState) -> CompilerState:
        """Runs the command to modify the compiler state."""
        raise NotImplementedError


class Loc:
    """Sets the loc pointer."""
    address: int

    def run(self, state: CompilerState) -> CompilerState:
        state.gci_pointer_mode = False
        state.patch_mode = False
        state.loc_pointer = self.address
        return state


@dataclass
class Gci:
    """Sets the gci pointer."""
    address: int

    def run(self, state: CompilerState) -> CompilerState:
        state.gci_pointer_mode = True
        state.patch_mode = False
        state.gci_pointer = self.address
        return state


@dataclass
class Patch:
    """Sets the patch pointer."""
    address: int

    def run(self, state: CompilerState) -> CompilerState:
        state.gci_pointer_mode = True
        state.patch_mode = True
        state.gci_pointer = self.address
        return state


@dataclass
class Add:
    """Adds to the currently-active pointer."""
    amount: int

    def run(self, state: CompilerState) -> CompilerState:
        if state.gci_pointer_mode:
            state.gci_pointer += self.amount
        else:
            state.loc_pointer += self.amount
        return state


@dataclass
class BaseWrite:
    """(Base class) Writes data to the write table."""
    data: bytes

    def run(self, state: CompilerState) -> CompilerState:
        entries = WriteEntryList(self.data, state, EMPTY_CONTEXT)
        if state.patch_mode:
            state.patch_table += entries
        else:
            self._check_collisions(state.write_table, entries)
            state.write_table += entries
        return state

    @staticmethod
    def _check_collisions(old_entries: list[WriteEntry], new_entries: list[WriteEntry]) -> None:
        """Checks for and warns about collisions in the write table."""
        for entry in new_entries:
            for prev_entry in old_entries:
                if entry.intersects(prev_entry):
                    logger.warning(f"GCI location 0x{max(prev_entry.address, entry.address):x} "
                                    "was already written to by {prev_entry.context.filepath.name} "
                                    "(Line {prev_entry.context.line_number+1}) and is being overwritten")
        return


class String(BaseWrite):
    """Writes a string as bytes to the write table."""

    def __init__(self, data: str):
        self.data = bytes(bytes(data, 'utf-8').decode("unicode_escape"), encoding='ascii')


class Fill(BaseWrite):
    """Writes a fill pattern to the write table."""

    def __init__(self, count: int, pattern: bytes):
        self.data = pattern * count


class BaseFile(BaseWrite):
    """(Base class) Writes a file to the write table."""

    def __init__(self, path: str, load_function: Callable[[Path], bytes]):
        self.path = Path(path).resolve()
        self._loadfunc = load_function

    def run(self, state: CompilerState) -> CompilerState:
        if not self.path in state.bin_files:
            state.bin_files[self.path] = self._loadfunc(self.path)
        return super().run(state)


class File(BaseFile):
    """Writes a binary file to the write table."""

    def __init__(self, path: str):
        super().__init__(path, files.load_bin_file)


class Asmsrc(BaseFile):
    """Writes a compiled version of an ASM source file to the write table."""

    def __init__(self, path: str):
        super().__init__(path, files.load_asm_file)


class Geckocodelist(BaseFile):
    """Writes a Gecko codelist file to the write table."""

    def __init__(self, path: str):
        super().__init__(path, files.load_geckocodelist_file)


class Src:
    """Sources and compiles an MGC file."""

    def __init__(self, path: str):
        self.path = Path(path).resolve()

        def run(self, state: CompilerState) -> CompilerState:
            if not self.path in state.mgc_files:
                state.mgc_files[self.path] = files.load_mgc_file(self.path)
            return state
