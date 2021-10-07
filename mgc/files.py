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


def bin_file(path: Path) -> bytes:
    """A binary file loaded from disk."""
    logger.info(f"Reading binary file {path.name}")
    data = _read_bin_file(path)
    return builder.build_binfile(data)


def asm_file(path: Path) -> bytes:
    """An ASM file loaded from disk and compiled into binary."""
    logger.info(f"Reading ASM source file {path.name}")
    data = _read_text_file(path)
    return builder.build_asmfile(data)


def gecko_file(path: Path) -> bytes:
    """A Gecko codelist file loaded from disk and compiled into binary."""
    logger.info(f"Reading Gecko codelist file {path.name}")
    data = _read_text_file(path)
    return builder.build_geckofile(path, data)


def mgc_file(path: Path) -> list:
    """An MGC file loaded from disk and parsed into a Command list."""
    logger.info(f"Reading MGC file {path.name}")
    data = _read_text_file(path)
    return builder.build_mgcfile(data)
