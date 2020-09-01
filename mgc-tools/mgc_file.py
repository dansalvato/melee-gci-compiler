"""mgc_file.py: A class that stores the data from an MGC file and sends lines
to the compiler when requested."""

class MGCFile:
	def __init__(filepath, filedata, ref_filepath=None, ref_line_number=None):
		self.filepath = filepath
		self.filedata = filedata
		self.ref_filepath = ref_filepath # The file that sourced this one
		self.ref_line_number = ref_line_number # The line number of the !src
		self.line_number = 0
		self.begin_line = 0
		self.end_line = 0

		# Search for !begin and !end
		for index, line in enumerate(filedata):
			line = line.lstrip().lower()
			if line.startswith('!begin'):
				self.begin_line = index + 2 # Begin on line after !begin
				self.line_number = self.begin_line
				break
		for index, line in enumerate(filedata):
			line = line.lstrip().lower()
			if line.startswith('!end'):
				self.end_line = index + 1 # end_line is !end
				break

	def nextline(self):
		"""Increments the line number and returns the next line in the file."""
		if self.line_number >= self.end_line: return "" # We've reached !end
		if self.line_number >= len(self.filedata): return "" # End of file
		self.line_number += 1
		return filedata[line_number - 1]