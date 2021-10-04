"""logger.py: Formats and logs messages to the console during MGC compilation."""

from pathlib import Path

LOGTYPE_NAMES = [
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR"
    ]

MAX_FILE_STRING_LENGTH = 30
_file_stack = []
silent_log = False
debug_log = False

def push_file(filepath: Path) -> None:
    """Adds a file path to use for log messages."""
    _file_stack.append(filepath)

def pop_file() -> None:
    """Removes the last file path used for log messages, such as when that file
    is done being processed."""
    if _file_stack:
        _file_stack.pop()

def log(logtype: str, message: str, line_number: int=None) -> None:
    """Prints a log message to the console with the relevant file path and line
    number."""
    if silent_log and not debug_log:
        return
    if logtype == 'DEBUG' and not debug_log:
        return
    filepath = _file_stack[-1] if _file_stack else None
    message = format_log(logtype, message, filepath, line_number)
    print(message)

def format_log(logtype: str, message: str, filepath: Path=None, line_number: int=None) -> str:
    """Returns a formatted log message."""
    if logtype not in LOGTYPE_NAMES:
        raise ValueError("Attempted to log with an unknown logtype.")
    if _file_stack:
        filepath = _file_stack[-1]
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
