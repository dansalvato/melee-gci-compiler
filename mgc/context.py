from dataclasses import dataclass
from pathlib import Path


@dataclass
class Context:
    """A file and line number responsible for the current operation.
    Usually, a new context is created before performing operations on a file,
    and done() is called once the operations are finished. Exceptions and
    other objects can reference context.top() to keep track of what file and
    line number was responsible for that operation."""

    def __init__(self, path: Path, line_number: int=-1):
        self.path = path
        self.line_number = line_number

    def __repr__(self):
        return f"{self.path.name} line {self.line_number+1}"

    def __enter__(self):
        _context_stack.append(self)
        return self

    def __exit__(self, type, value, traceback):
        # If receiving an Exception, preserve the context stack
        if type is not None:
            return
        # Otherwise, remove us from the top of the context stack
        if _context_stack[-1] is not self:
            raise IndexError(f"Attempting to remove a non-top-level context: {self}")
        else:
            _context_stack.pop()

    def copy(self) -> 'Context':
        return Context(self.path, self.line_number)

_context_stack = []
EMPTY_CONTEXT = Context(Path())
_context_stack.append(EMPTY_CONTEXT)


def in_stack(path: Path) -> bool:
    """Determines whether a given path is already in the context stack."""
    return path in [c.path for c in _context_stack]


def top() -> Context:
    """Returns the top context to use for log messages."""
    return _context_stack[-1].copy()


def root() -> Context:
    """Returns the root context."""
    if len(_context_stack) > 1:
        return _context_stack[1]
    else:
        return _context_stack[0]

