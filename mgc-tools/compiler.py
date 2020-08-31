"""compiler.py: Compiles MGC files into a block of data that is ready to write
to the GCI."""
from pathlib import Path
from log import *
from mgc_file import MGCFile

# The earliest location we can inject data into the GCI
GCI_START_OFFSET = 0x2060

# If a GCI file is given to the compiler, this will be replaced with that file
gci_data = bytearray(0x15850)

# Dict that contains each opcode name and the function that handles it
OPCODES = {
	'loc': None,
	'gci': None,
	'src': None,
	'ascii': None,
	'asm': None,
	'asmend': None,
	'c2': None,
	'c2end': None,
	'geckocodelist': None,
	'begin': None, # Compiler only finds this if defined twice; log warning
	'end': None, # Compiler only finds this if defined twice; log warning
	}

# A dict that contains all loaded MGC filedata, accessible by filename.
# We load all MGC files from disk ahead of time and use this dict to send
# file data to any MGCFile objects we create.
mgc_filedata = {}

# A list of the current MGC file stack if there are nested source files
mgc_stack = []

# The directory of the root MGC file
root_directory = ""

def load_mgc_file(filename):
	"""Loads a MGC file from disk and stores its data in mgc_filedata"""
	# Sanitize file name
	filename = str(Path(filename).absolute())
	if filename in mgc_filedata: return [] # Do nothing if the file is already loaded
	filedata = []
	with open(filename, 'r') as f:
		filedata = f.readlines()
	mgc_filedata[filename] = filedata
	# See if the new file sources any additional files we need to load
	# This ignores !begin and !end; any !src gets loaded from disk
	additional_files = []
	for line in filedata:
		opcode = get_opcode(line)
		if opcode.type != 'src' and opcode.type != 'geckocodelist': continue
		additional_files.append(root_directory + opcode.data)
	return additional_files

def load_all_mgc_files(root_filename):
	"""Loads all required MGC files from disk, starting with the root file"""
	additional_files = load_mgc_file(root_filename)
	# This shouldn't infinite loop because already-loaded files return None
	for filename in additional_files:
		additional_files.append(load_mgc_file(filename))
