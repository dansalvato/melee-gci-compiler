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

import sys
import subprocess
from pathlib import Path
from .errors import CodetypeError, UnsupportedOSError

eabi = {}

def setup():

    # Simple check to help prevent this from being run multiple times
    if eabi: return

    bin_root = Path(__file__).parent/"bin"
    # Pathnames for powerpc-eabi executables
    file_extension = ''
    if sys.platform == "linux":
        if sys.maxsize > 2**32:
            platform_folder = "linux_x86_64"
        else:
            platform_folder = "linux_i686"
    elif sys.platform == "darwin":
        platform_folder = "darwin"
    elif sys.platform == "win32":
        platform_folder = "win32"
        file_extension = ".exe"
    eabi['as'] = bin_root/platform_folder/("powerpc-eabi-as" + file_extension)
    eabi['ld'] = bin_root/platform_folder/("powerpc-eabi-ld" + file_extension)
    eabi['objcopy'] = bin_root/platform_folder/("powerpc-eabi-objcopy" + file_extension)

def asm_opcodes(tmpdir, txtfile=None, binfile=None):
    if sys.platform not in ("darwin", "linux2", "win32"):
        raise UnsupportedOSError("'" + sys.platform + "' os is not supported")
    for i in ("as", "ld", "objcopy"):
        if not eabi[i].exists():
            raise IOError(eabi[i].name + " not found")

    if txtfile is None:
        txtfile = tmpdir.joinpath("code.txt")
    if binfile is None:
        binfile = tmpdir.joinpath("code.bin")
    src1file = tmpdir.joinpath("src1.o")
    src2file = tmpdir.joinpath("src2.o")

    output = subprocess.Popen([str(eabi["as"]), "-mregnames", "-mgekko", "-o", 
        str(src1file), str(txtfile)], stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE).communicate()

    if output[1]:
        errormsg = output[1]
        raise RuntimeError(errormsg)

    subprocess.Popen([str(eabi["ld"]), "-Ttext", "0x80000000", "-o", 
        str(src2file), str(src1file)], stderr=subprocess.PIPE).communicate()
    subprocess.Popen([str(eabi["objcopy"]), "-O", "binary", 
        str(src2file), binfile], stderr=subprocess.PIPE).communicate()
    
    with open(binfile, "rb") as f:
        rawhex = f.read().hex()
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
            pre += "3" + bapo[2:]
        else:
            pre += "2" + bapo[2:]
        
        if ctype == "C2D2":
            pre += numlines
            return pre + rawhex + post
        else: # ctype == "F2F4"
            if int(numlines, 16) <= 0xFF:
               pre = "F" + str(int({"D":"2"}.get(pre[0], "0")) + int(pre[1]))
               if int(numlines, 16) <= 0xF:
                   numlines = "0"+numlines

               pre += bapo[2:] + " " + chksum + xor + numlines
               return pre + rawhex + post
            else:
               raise CodetypeError("Number of lines (" + 
                       numlines + ") must be lower than 0xFF")


setup()
