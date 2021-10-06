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


def load_geckocodelist_file(path: Path) -> bytes:
    """Loads a Gecko codelist file from disk and stores its data in
    bin_files"""
    logger.info(f"Reading Gecko codelist file {path.name}")
    data = _read_text_file(path)
    return builder.build_geckofile(path, data)


def load_bin_file(path: Path) -> bytes:
    """Loads a binary file from disk and stores its data in bin_files"""
    logger.info(f"Reading binary file {path.name}")
    data = _read_bin_file(path)
    return builder.build_binfile(data)


def load_asm_file(path: Path) -> bytes:
    """Loads an ASM code file from disk and stores its data in bin_files
       (it gets compiled to binary as we load it from disk)"""
    logger.info(f"Reading ASM source file {path.name}")
    data = _read_text_file(path)
    return builder.build_asmfile(data)


def load_mgc_file(path: Path) -> list:
    """Loads a MGC file from disk and stores its data in mgc_files"""
    logger.info(f"Reading MGC file {path.name}")
    data = _read_text_file(path)
    newfile = builder.build_mgcfile(data)
    return newfile

