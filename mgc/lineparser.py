"""lineparser.py: Searches text for opcodes and returns appropriate data"""
import string
from collections import namedtuple

CODETYPES = [
    'BIN',
    'HEX',
    'COMMAND',
    'WARNING',
    'ERROR',
    ]
COMMANDS = {
    # List of each command and its expected number and type of args
    'loc': [int],
    'gci': [int],
    'add': [int],
    'src': [str],
    'file': [str],
    'geckocodelist': [str],
    'string': [str],
    'asm': [],
    'asmend': [],
    'c2': [int],
    'c2end': [],
    'begin': [],
    'end': [],
    'echo': [str],
    }

Operation = namedtuple('Operation', ['codetype', 'data'], defaults=[None, None])
Command = namedtuple('Command', ['name', 'args'], defaults=[None, []])
# Generic errors
SYNTAX_ERROR = Operation('ERROR', "Invalid syntax")

def parse_opcodes(script_line):
    """Parses a script line and returns a list of opcodes and data found."""
    op_list = []
    # If the line is empty, we're done
    if script_line == '':
        return op_list

    # Check if line is hex
    if script_line[0] in string.hexdigits:
        # Remove all whitespace
        script_line = script_line.translate(dict.fromkeys(map(ord, string.whitespace)))
        try:
            int(script_line, 16)
            padding = len(script_line) % 2
            if padding > 0:
                op_list.append(Operation('WARNING', 'Hex data is not byte-aligned; padding to the nearest byte'))
                script_line = '0' + script_line
            op_list.append(Operation('HEX', script_line))
        except ValueError:
            op_list.append(SYNTAX_ERROR)
    # Check if line is binary
    elif script_line[0] == '%':
        # Remove % character
        script_line = script_line[1:]
        # Remove all whitespace
        script_line = script_line.translate(dict.fromkeys(map(ord, string.whitespace)))
        try:
            int(script_line, 2)
            padding = len(script_line) % 8
            if padding > 0:
                op_list.append(Operation('WARNING', 'Binary data is not byte-aligned; padding to the nearest byte'))
                script_line = '0' * (8 - padding) + script_line
            op_list.append(Operation('BIN', script_line))
        except ValueError:
            op_list.append(SYNTAX_ERROR)

    # Check if line is a command
    elif script_line[0] == '!':
        # Check that all quotes are closed
        if script_line.count('"') % 2 == 1:
            op_list.append(SYNTAX_ERROR)
        else:
            command_args = script_line.split(' ')
            command_name = command_args.pop(0)[1:]
            # If command contains quotes, we ignore command_args
            # TODO: Enforce correct number of args even if command has quotes
            command_quotes = script_line.split('"')[1::2]
            if command_quotes:
                # Re-add the quotes so compiler can enforce them
                command_quotes = [f'"{s}"' for s in command_quotes]
                command_args = command_quotes
            # Send the Command for data validation
            validated_commands = _parse_command(Command(command_name, command_args))
            op_list += validated_commands


    # We've exhausted all opcodes
    else:
        op_list.append(SYNTAX_ERROR)


    return op_list

def _parse_command(command):
    """Takes a Command and validates the arguments and data types.
       Returns in a list a COMMAND operation with any WARNING or ERROR
       Operations to go with it."""
    # Make sure the COMMAND operation has a Command as data
    if not isinstance(command, Command):
        raise ValueError("COMMAND operation has invalid data")
    # Check for known command name
    if not command.name in COMMANDS:
        return [Operation('ERROR', "Unknown command")]
    # Check for correct number of args
    arg_count = len(command.args)
    expected_arg_count = len(COMMANDS[command.name])
    if arg_count != expected_arg_count:
        return [Operation('ERROR', f"Command expected {expected_arg_count} arg(s) but received {arg_count}")]
    op_list = []
    untyped_args = command.args
    typed_args = []
    expected_types = COMMANDS[command.name] # List of arg types for this Command
    for index, arg in enumerate(untyped_args):
        expected_type = expected_types[index]
        if expected_type == str:
            # String arguments must be surrounded by quotes
            if arg[0] != '"' or arg[len(arg)-1] != '"':
                return [Operation('ERROR', f"Command argument {index+1} must be a string")]
            # For strings, just append our Command as-is because data is
            # already a string, but the quotes are no longer needed
            typed_args.append(arg.replace('"', ''))
        elif expected_type == int:
            # As of now, int type always means hex
            try:
                typed_arg = int(arg, 16)
                typed_args.append(typed_arg)
            except ValueError:
                return [Operation('ERROR', f"Command argument {index+1} must be a hex value")]

    return [Operation('COMMAND', Command(command.name, typed_args))]
