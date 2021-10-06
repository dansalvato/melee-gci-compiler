"""logger.py: Formats and logs messages to the console during MGC compilation."""

from pathlib import Path
from . import context

MAX_FILE_STRING_LENGTH = 30
silent_log = False
debug_log = False

def debug(message: str, line_number: int=None) -> None:
    _log('DEBUG', message, line_number)

def info(message: str, line_number: int=None) -> None:
    _log('INFO', message, line_number)

def warning(message: str, line_number: int=None) -> None:
    _log('WARNING', message, line_number)

def error(message: str, line_number: int=None) -> None:
    _log('ERROR', message, line_number)

def _log(logtype: str, message: str, line_number: int=None) -> None:
    """Prints a log message to the console with the relevant file path and line
    number."""
    if silent_log and not debug_log:
        return
    if logtype == 'DEBUG' and not debug_log:
        return
    c = context.top()
    if c is not context.EMPTY_CONTEXT:
        filepath = c.path
        line = c.line_number
    else:
        filepath = None
        line = line_number
    message = _format_log(logtype, message, filepath, line)
    print(message)

def _format_log(logtype: str, message: str, filepath: Path=None, line_number: int=None) -> str:
    """Returns a formatted log message."""
    file_string = _format_filepath(filepath, line_number)
    message = f"[{logtype}]{' ' * (9 - len(logtype))}{file_string}{message}"
    return message

def _format_filepath(filepath: Path=None, line_number: int=None) -> str:
    """Returns a formatted string out of a file path and line number."""
    file_string = ''
    if filepath:
        file_string = str(filepath)
        if len(file_string) > MAX_FILE_STRING_LENGTH:
            root_string = filepath.parts[0]
            file_string = root_string + "..." + file_string[-(MAX_FILE_STRING_LENGTH-3) + len(root_string):]
        if line_number is not None:
            file_string += f", Line {str(line_number + 1)}"
        file_string = f"[{file_string}]" + ' '
    return file_string
