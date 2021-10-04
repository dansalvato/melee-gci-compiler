from .logger import format_log

class CompileError(Exception):
    """Raised when there is a syntax, data, or other error in the MGC script"""
    def __init__(self, value, line_number=None):
        self.value = value
        self.line_number = line_number
