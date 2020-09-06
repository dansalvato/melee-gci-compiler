from logger import format_log

class CompileError(Exception):
    """Raised when there is a syntax, data, or other error in the MGC script"""
    def __init__(self, value, mgc_file=None, line_number=None):
        self.value = value
        self.mgc_file = mgc_file
        self.line_number = line_number
    def __str__(self):
        return format_log('ERROR', self.value, self.mgc_file, self.line_number)