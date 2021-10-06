from dataclasses import dataclass
from pathlib import Path
from typing import Optional


_context_stack = []


@dataclass
class Context:
    """A file and line number responsible for the current operation."""

    def __init__(self, path: Path, line_number: Optional[int]=None):
        self.path = path
        self.line_number = line_number
        _context_stack.append(self)

    def __repr__(self):
        return f"{self.path.name} line {self.line_number}"

    def done(self) -> None:
        """Call when finished with the current context to remove it."""
        if _context_stack[-1] is not self:
            raise IndexError("Attempting to remove a non-top-level context")
        else:
            _context_stack.pop()


def top() -> Optional[Context]:
    """Returns the top context to use for log messages."""
    return _context_stack[-1] if _context_stack else None


def root() -> Optional[Context]:
    """Returns the root context."""
    return _context_stack[0] if _context_stack else None

