from pathlib import Path
from . import logger
from . import builder
from .errors import CompileError


def _read_bin_file(filepath: Path) -> bytes:
    """Reads a binary file from disk and returns the byte array"""
    try:
        with filepath.open('rb') as f:
            filedata = f.read()
    except FileNotFoundError:
        raise CompileError(f"File not found: {str(filepath)}")
    return filedata


def _read_text_file(filepath: Path) -> list[str]:
    """Reads a text file from disk and returns a list of each line of data"""
    try:
        with filepath.open('r') as f:
            filedata = f.readlines()
    except FileNotFoundError:
        raise CompileError(f"File not found: {str(filepath)}")
    except UnicodeDecodeError:
        raise CompileError("Unable to read file; make sure it's a text file")
    return filedata


def load_geckocodelist_file(filepath: Path) -> bytes:
    """Loads a Gecko codelist file from disk and stores its data in
    bin_files"""
    logger.info(f"Reading Gecko codelist file {filepath.name}")
    filedata = _read_text_file(filepath)
    return builder.build_geckofile(filedata)


def load_bin_file(filepath: Path) -> bytes:
    """Loads a binary file from disk and stores its data in bin_files"""
    logger.info(f"Reading binary file {filepath.name}")
    filedata = _read_bin_file(filepath)
    return builder.build_binfile(filedata)


def load_asm_file(filepath: Path) -> bytes:
    """Loads an ASM code file from disk and stores its data in bin_files
       (it gets compiled to binary as we load it from disk)"""
    logger.info(f"Reading ASM source file {filepath.name}")
    filedata = _read_text_file(filepath)
    return builder.build_asmfile(filedata)


def load_mgc_file(filepath: Path) -> list:
    """Loads a MGC file from disk and stores its data in mgc_files"""
    logger.info(f"Reading MGC file {filepath.name}")
    filedata = _read_text_file(filepath)
    newfile = builder.build_mgcfile(filedata)
    return newfile

