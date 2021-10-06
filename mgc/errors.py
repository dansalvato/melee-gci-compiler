from .context import Context
from dataclasses import dataclass


class CompileError(Exception):
    """Raised when there is a syntax, data, or other error in the MGC script"""
    def __init__(self, value, line_number=None, context=None):
        self.value = value
        self.line_number = line_number
        if context:
            self.line_number = context.line_number


@dataclass
class BuildError(Exception):
    """Raised when there is an error during a file building process."""
    message: str

