"""mgc_file.py: A class that stores the data from an MGC file and sends lines
to the compiler when requested."""
from typing import List, Tuple

class MGCFile:
	def __init__(filename: str, filedata: List[str]):
		self.filename = filename
		self.filedata = filedata
		self.line_number = 0

	def nextline(self):
		"""Increments the line number and returns the next line in the file."""
		if self.line_number >= len(self.filedata): return "" # End of file
		self.line_number += 1
		return filedata[line_number - 1]