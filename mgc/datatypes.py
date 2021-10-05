"""Contains custom data classes that are used throughout compilation."""

from typing import NamedTuple
from pathlib import Path


class Context(NamedTuple):
    """A file and line number responsible for the current operation."""
    filepath: Path
    line_number: int

EMPTY_CONTEXT = Context(Path('UNKNOWN_FILE'), -1)


class WriteEntry(NamedTuple):
    """An entry of data to write to the GCI."""
    address: int
    data: bytes
    context: 'Context' = EMPTY_CONTEXT

    def __len__(self):
        return len(self.data)

    def intersects(self, entry: 'WriteEntry') -> bool:
        """Tests if two WriteEntries intersect with each other."""
        return ((self.address <= entry.address and
                 self.address + len(self.data) > entry.address) or
                (entry.address <= self.address and
                 entry.address + len(entry.data) > self.address))

