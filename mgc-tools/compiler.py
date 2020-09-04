"""compiler.py: Compiles MGC files into a block of data that is ready to write
to the GCI."""
from pathlib import Path
from logger import *
from lineparser import *
from mgc_file import MGCFile

# The earliest location we can inject data into the GCI
GCI_START_OFFSET = 0x2060

# If a GCI file is given to the compiler, this will be replaced with that file
gci_data = bytearray(0x15850)

# The latest !loc pointer
loc_pointer = 0

# This is True if the !gci opcode was used
gci_pointer_mode = False

# Dict that contains each opcode name and the function that handles it
OPCODES = {
	'loc': None,
	'gci': None,
	'src': None,
	'file': None,
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

# This gets set to True if the compiler hits an unrecoverable error
stop_compile = False

def load_mgc_file(filepath):
	"""Loads a MGC file from disk and stores its data in mgc_filedata"""
	if filepath in mgc_filedata: return [] # Do nothing if the file is already loaded
	filedata = []
	with filepath.open('r') as f:
		filedata = f.readlines()
	mgc_filedata[filepath] = filedata
	# See if the new file sources any additional files we need to load
	# This ignores !begin and !end; any !src gets loaded from disk
	additional_files = []
	for line in filedata:
		opcode = get_opcode(line)
		if opcode.type != 'src' and opcode.type != 'geckocodelist': continue
		additional_files.append(Path(root_directory + opcode.data).absolute())
	return additional_files

def load_all_mgc_files(root_filepath):
	"""Loads all required MGC files from disk, starting with the root file"""
	additional_files = load_mgc_file(root_filepath)
	# This shouldn't infinite loop because already-loaded files return None
	for path in additional_files:
		additional_files.append(load_mgc_file(path))
