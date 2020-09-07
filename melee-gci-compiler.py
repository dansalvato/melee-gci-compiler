#!/usr/bin/env python3
"""melee-gci-compiler.py: Compiles custom data into Melee GCI save files using
   MGC script files"""

import sys, getopt
from pathlib import Path
from mgc import compiler
import mgc.logger as logger
from mgc.logger import log
from mgc.errors import CompileError

USAGE_TEXT = """\
Usage: melee-gci-compiler.py [options] <script_path>

<script_path>  The path to the MGC script file you want to compile.
-i             Any Melee GCI file. Required to generate a usable Melee save.
-o             The GCI file to output. If omitted, no data will be written.
-h, --help     Displays this usage text.
--noclean      Do not clean/initialize the input GCI file before compiling.
--silent       Suppress command line output, except for fatal errors.
--debug        Output extra information while compiling and on errors.
"""


def main(argv):
    script_path = None
    input_gci = None
    output_gci = None
    noclean = False
    silent = False
    debug = False
    logger.silent_log = silent
    try:
        opts, args = getopt.getopt(argv[1:],'i:o:h',['help','noclean','silent','debug'])
    except getopt.GetoptError:
        print(USAGE_TEXT)
        sys.exit(2)
    if len(args) != 1:
        print(USAGE_TEXT)
        sys.exit(2)
    script_path = args[0]
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(USAGE_TEXT)
            sys.exit()
        elif opt == '-i': input_gci = arg
        elif opt == '-o': output_gci = arg
        elif opt == '--noclean': noclean = True
        elif opt == '--silent': silent = True
        elif opt == '--debug': debug = True
        else:
            print(USAGE_TEXT)
            sys.exit(2)

    try:
        gci_data = compiler.compile(script_path, input_gci=input_gci, noclean=noclean, silent=silent, debug=debug)
    except CompileError as e:
        if debug: raise
        else:
            print(e)
            sys.exit(10)
    log('INFO', "Compile successful")
    if not output_gci: log('INFO', "No output GCI specified; no files will be written")
    elif not input_gci: log('INFO', "No input GCI specified; writing raw data to file")
    else: log('INFO', "Writing final GCI file")
    if output_gci:
        try:
            with open(output_gci, 'wb') as f:
                f.write(gci_data)
        except Exception as e:
            if debug: raise
            else: log('ERROR', f"Couldn't write GCI file: {e}")
    log('INFO', "Successfully finished all tasks")
    sys.exit()




if __name__ == "__main__":
    main(sys.argv)