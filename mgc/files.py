from pathlib import Path
from . import logger
from . import builder
from .errors import CompileError


def _read_bin_file(path: Path) -> bytes:
    """Reads a binary file from disk and returns the byte array"""
    try:
        with path.open('rb') as f:
            data = f.read()
    except FileNotFoundError:
        raise CompileError(f"File not found: {str(path)}")
    return data


def _read_text_file(path: Path) -> list[str]:
    """Reads a text file from disk and returns a list of each line of data"""
    try:
        with path.open('r') as f:
            data = f.readlines()
    except FileNotFoundError:
        raise CompileError(f"File not found: {str(path)}")
    except UnicodeDecodeError:
        raise CompileError("Unable to read file; make sure it's a text file")
    return data


class BinFile:
    """A binary file loaded from disk."""

    def __init__(self, path: Path):
        logger.info(f"Reading binary file {path.name}")
        data = _read_bin_file(path)
        self.data = builder.build_binfile(data)


class AsmFile(BinFile):
    """An ASM file loaded from disk and compiled into binary."""

    def __init__(self, path: Path):
        logger.info(f"Reading ASM source file {path.name}")
        data = _read_text_file(path)
        self.data = builder.build_asmfile(data)


class GeckoFile(BinFile):
    """A Gecko codelist file loaded from disk and compiled into binary."""

    def __init__(self, path: Path):
        logger.info(f"Reading Gecko codelist file {path.name}")
        data = _read_text_file(path)
        self.data = builder.build_geckofile(path, data)


class MgcFile:
    """An MGC file loaded from disk and parsed into a Command list."""

    def __init__(self, path: Path):
        logger.info(f"Reading MGC file {path.name}")
        data = _read_text_file(path)
        self.commands = builder.build_mgcfile(data)
