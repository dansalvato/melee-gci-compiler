"""log.py: Formats and logs messages to the console during MGC compilation."""
from enum import Enum

class LogType(Enum):
	DEBUG = 0
	INFO = 1
	WARNING = 2
	ERROR = 3

LOGTYPE_NAMES = [
	"DEBUG",
	"INFO",
	"WARNING",
	"ERROR"
	]

def log(logtype, message, mgc_file=None):
	"""Prints a log message to the console with the relevant MGC file and line
	number."""
	if logtype.value >= len(LOGTYPE_NAMES):
		raise ValueError("Attempted to log with an unknown logtype.")
	message = "{0}:  {1}".format(LOGTYPE_NAMES[logtype.value], message)
	print(message)