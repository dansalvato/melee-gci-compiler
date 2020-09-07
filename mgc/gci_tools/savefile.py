#!/usr/bin/python3
""" savefile - example script for [un]packing a save file. """

import os, sys
import struct

from .meleegci import *

print(sys.argv)
if len(sys.argv) < 4:
    print("Usage: savefile.py [--pack | --unpack] <input GCI> <output GCI>")
    print("[Un]pack the input GCI and save the contents to some output file.")
    exit(0)
else:
    flag = sys.argv[1]
    input_fn = sys.argv[2]
    output_fn = sys.argv[3]

# -----------------------------------------------------------------------------

if (flag == "--unpack"):
    input_gci = melee_gamedata(input_fn, packed=True)
    print("[*] Read GCI: {}".format(input_gci.get_filename()))
    input_gci.unpack()

elif (flag == "--pack"):
    input_gci = melee_gamedata(input_fn, packed=False)
    print("[*] Read GCI: {}".format(input_gci.get_filename()))
    input_gci.recompute_checksums()
    input_gci.pack()

else:
    print("Usage: savefile.py [--pack | --unpack] <input GCI> <output GCI>")
    exit(0)


# -----------------------------------------------------------------------------
# Write the new GCI to a file

print("Writing to {}".format(output_fn))
ofd = open(output_fn, "wb")
ofd.write(input_gci.raw_bytes)
ofd.close()
