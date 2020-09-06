"""logger.py: Formats and logs messages to the console during MGC compilation."""

LOGTYPE_NAMES = [
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR"
    ]

MAX_FILE_STRING_LENGTH = 30
silent_log = False

def log(logtype, message, mgc_file=None, line_number=None):
    """Prints a log message to the console with the relevant MGC file and line
    number."""
    global silent_log
    if silent_log: return
    if logtype not in LOGTYPE_NAMES:
        raise ValueError("Attempted to log with an unknown logtype.")
    file_string = ''
    line_string = ''
    if mgc_file:
        filepath = mgc_file.filepath
        file_string = str(filepath)
        if len(file_string) > MAX_FILE_STRING_LENGTH:
            root_string = filepath.parts[0]
            file_string = root_string + "..." + file_string[-(MAX_FILE_STRING_LENGTH-3) + len(root_string):]
        if line_number:
            line_string = ", Line " + str(line_number + 1)
        file_string = '[' + file_string + line_string + '] '
    message = f"[{logtype}]   {file_string}{message}"
    print(message)
    return
