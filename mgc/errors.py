from dataclasses import dataclass


@dataclass
class CompileError(Exception):
    """Raised when there is an error during execution of script commands."""
    message: str


class BuildError(CompileError):
    """Raised when there is an error during a file building process."""
    pass

