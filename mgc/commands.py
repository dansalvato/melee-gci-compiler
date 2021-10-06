from abc import abstractmethod
from typing import Protocol
from dataclasses import dataclass
from pathlib import Path
from .datatypes import CompilerState
from .datatypes import WriteEntry, WriteEntryList
from .errors import CompileError
from . import logger
from . import files


class Command(Protocol):
    """Basic representation of an MGC command operation."""

    @abstractmethod
    def run(self, state: CompilerState) -> CompilerState:
        """Runs the command to modify the compiler state."""
        raise NotImplementedError


@dataclass
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
        entries = WriteEntryList(self.data, state)
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


class HexString(BaseWrite):
    """Writes a hex string as bytes to the write table."""

    def __init__(self, data: str):
        self.data = bytes.fromhex(data)


class BinaryString(BaseWrite):
    """Writes a binary string as bytes to the write table."""

    def __init__(self, data: str):
        data_hex = format(int(data, 2), 'x')
        if len(data_hex) % 2 > 0:
            data_hex = '0' + data_hex
        self.data = bytes.fromhex(data)


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

    def __init__(self, path: str, filetype: type[files.BinFile]):
        self.path = Path(path).resolve()
        self.filetype = filetype

    def run(self, state: CompilerState) -> CompilerState:
        if not self.path in state.bin_files:
            state.bin_files[self.path] = self.filetype(self.path)
        return super().run(state)


class Bin(BaseFile):
    """Writes a binary file to the write table."""

    def __init__(self, path: str):
        super().__init__(path, files.BinFile)


class Asmsrc(BaseFile):
    """Writes a compiled version of an ASM source file to the write table."""

    def __init__(self, path: str):
        super().__init__(path, files.AsmFile)


class Geckocodelist(BaseFile):
    """Writes a Gecko codelist file to the write table."""

    def __init__(self, path: str):
        super().__init__(path, files.GeckoFile)


class Src:
    """Sources and compiles an MGC file."""

    def __init__(self, path: str):
        self.path = Path(path).resolve()

    def run(self, state: CompilerState) -> CompilerState:
        if not self.path in state.mgc_files:
            state.mgc_files[self.path] = files.MgcFile(self.path)
            # TODO: Run compile method here
        return state


class Asm(BaseWrite):
    """Write a compiled version of an ASM block to the write table."""
    pass
class C2(BaseWrite):
    """Write a compiled version of a C2 ASM block to the write table."""
    pass


class Blockorder:
    """Changes the order that blocks get arranged in the GCI file."""

    def __init__(self, b0: int, b1: int, b2: int, b3: int, b4: int,
                       b5: int, b6: int, b7: int, b8: int, b9: int):
        self._blockorder = [b0, b1, b2, b3, b4, b5, b6, b7, b8, b9]
        for b in self._blockorder:
            if b < 0:
                raise CompileError("Block number cannot be negative")
            elif b > 9:
                raise CompileError("Block number cannot be greater than 9")

    def run(self, state: CompilerState) -> CompilerState:
        state.block_order = self._blockorder
        return state


@dataclass
class Echo:
    """Logs a message."""
    message: str

    def run(self, state: CompilerState) -> CompilerState:
        logger.info(self.message)
        return state



@dataclass
class NotRunnable:
    """(Base class) Orphaned non-runnable builder commands that throw an error
    when attempting to run."""
    message: str

    def run(self, state: CompilerState) -> CompilerState:
        raise CompileError(self.message)


class AsmEnd(NotRunnable):
    """Not runnable. Signifies the end of an ASM block."""
    def __init__(self):
        self.message = "!asmend is used without a !asm preceding it"
class C2End(NotRunnable):
    """Not runnable. Signifies the end of a C2 ASM block."""
    def __init__(self):
        self.message = "!c2end is used without a !c2 preceding it"
class MacroEnd(NotRunnable):
    """Not runnable. Signifies the end of a macro block."""
    def __init__(self):
        self.message = "!macroend is used without a !macro preceding it"
class Begin(NotRunnable):
    """Not runnable. Signifies the beginning of an MGC script."""
    def __init__(self):
        self.message = "!begin is used more than once in this file"
class End(NotRunnable):
    """Not runnable. Signifies the end of an MGC script."""
    def __init__(self):
        self.message = "!end is used more than once in this file"
