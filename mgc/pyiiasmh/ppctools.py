#  PyiiASMH (ppctools.py)
#  Copyright (c) 2011, 2012, Sean Power
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the names of the authors nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#   
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL SEAN POWER BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
import time
import shutil
import logging
import binascii
import subprocess

from pathlib import Path
from .errors import CodetypeError, UnsupportedOSError

log = None
eabi = {}
vdappc = ""

def setup():
    global eabi, vdappc, log

    # Simple check to help prevent this from being run multiple times
    if log is not None or eabi != {} or vdappc != "":
        return

    here = Path(__file__).parent
    # Pathnames for powerpc-eabi executables
    # TODO: Refactor this to use pathlib
    for i in ("as", "ld", "objcopy"):
        eabi[i] = str(here/"lib"/sys.platform)

        if sys.platform == "linux2":
            if sys.maxint > 2**32:
                eabi[i] += "_x86_64"
            else:
                eabi[i] += "_i686"

        eabi[i] += "/powerpc-eabi-" + i

        if sys.platform == "win32":
            eabi[i] += ".exe"

    # Pathname for vdappc executable
    vdappc = str(here/"lib"/sys.platform)

    if sys.platform == "linux2":
        if sys.maxint > 2**32:
            vdappc += "_x86_64"
        else:
            vdappc += "_i686"

    vdappc += "/vdappc"

    if sys.platform == "win32":
        vdappc += ".exe"

    log = logging.getLogger("PyiiASMH")
    #hdlr = logging.FileHandler("error.log")
    formatter = logging.Formatter("\n%(levelname)s (%(asctime)s): %(message)s")
    #hdlr.setFormatter(formatter)
    #log.addHandler(hdlr)

def asm_opcodes(tmpdir, txtfile=None, binfile=None):
    if sys.platform not in ("darwin", "linux2", "win32"):
        raise UnsupportedOSError("'" + sys.platform + "' os is not supported")
    for i in ("as", "ld", "objcopy"):
        if not os.path.isfile(eabi[i]):
            raise IOError(eabi[i] + " not found")

    if txtfile is None:
        txtfile = tmpdir.joinpath("code.txt")
    if binfile is None:
        binfile = tmpdir.joinpath("code.bin")
    src1file = tmpdir.joinpath("src1.o")
    src2file = tmpdir.joinpath("src2.o")

    output = subprocess.Popen([eabi["as"], "-mregnames", "-mgekko", "-o", 
        str(src1file), str(txtfile)], stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE).communicate()
    #time.sleep(.25)

    if output[1]:
        errormsg = output[1]
        #errormsg = output[1].replace(txtfile + ":", "")
        #errormsg = errormsg.replace(" Assem", "Assem", 1)
        raise RuntimeError(errormsg)

    subprocess.Popen([eabi["ld"], "-Ttext", "0x80000000", "-o", 
        str(src2file), str(src1file)], stderr=subprocess.PIPE).communicate()
    #time.sleep(.25)
    subprocess.Popen([eabi["objcopy"], "-O", "binary", 
        str(src2file), binfile], stderr=subprocess.PIPE).communicate()
    #time.sleep(.25)
    
    # TODO: Pass these exceptions back to the compiler, don't handle here
    rawhex = ""
    try:
        f = open(binfile, "rb")
    except IOError:
        log.exception("Failed to open '" + binfile + "'")
        rawhex = "Something went wrong, please try again.\n"
    else:
        try:
            f.seek(0)
            rawhex = f.read().hex()
            #rawhex = format_rawhex(rawhex).upper()
        except IOError:
            log.exception("Failed to read '" + binfile + "'")
            rawhex = "Something went wrong, please try again.\n"
        except TypeError as e:
            log.exception(e)
            rawhex = "Something went wrong, please try again.\n"
        finally:
            f.close() 
    finally:
        return rawhex

def construct_code(rawhex, bapo=None, xor=None, chksum=None, ctype=None):
    if ctype is None:
        return rawhex

    numlines = int(len(rawhex) / 16) + 1

    if len(rawhex) % 16 > 0:
        post = "00000000"
    else:
        post = "6000000000000000"

    numlines = ("%08x" % numlines).upper()
    if ctype == "C0":
        pre = "C0000000%s" % (numlines)
        post = "4E800020" + post[8:]
        return pre + rawhex + post
    else:
        if bapo[0] not in ("8", "0") or bapo[1] not in ("0", "1"):
            raise CodetypeError("Invalid bapo '" + bapo[:2] + "'")

        pre = {"8":"C", "0":"D"}.get(bapo[0], "C")
        if bapo[1] == "1":
            pre += "3" + bapo[2:]# + " "
        else:
            pre += "2" + bapo[2:]# + " "
        
        if ctype == "C2D2":
            pre += numlines
            return pre + rawhex + post
        else: # ctype == "F2F4"
            if int(numlines, 16) <= 0xFF:
               pre = "F" + str(int({"D":"2"}.get(pre[0], "0")) + int(pre[1]))
               if int(numlines, 16) <= 0xF:
                   numlines = "0"+numlines

               pre += bapo[2:] + " " + chksum + xor + numlines# + "\n"
               return pre + rawhex + post
            else:
               raise CodetypeError("Number of lines (" + 
                       numlines + ") must be lower than 0xFF")


setup()
