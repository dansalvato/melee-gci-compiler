""" meleegci.py - interfaces for manipulating Melee savefiles """

import os
import struct

from .gci_encode import decode_byte as unpack
from .gci_encode import encode_byte as pack
from ..logger import log

class melee_gci(object):
    """ Base class for GCI files. Just basic setter/getter stuff for dentry
        data, and some machinery for reading files """

    def __init__(self, filename=None, raw_bytes=None, packed=None):
        if filename:
            self._filename = os.path.basename(filename).split(".")[0]
            self.raw_bytes = bytearray()
            try:
                with open(filename, "rb") as fd:
                    self.raw_bytes = bytearray(fd.read())
                self.filesize = len(self.raw_bytes)
                self.packed = packed
                log('DEBUG', "Read {} bytes from input GCI".format(hex(self.filesize)))
            except FileNotFoundError as e:
                err(e)
                self.raw_bytes = None
                self.filesize = None
                return None
        elif raw_bytes:
            self.raw_bytes = raw_bytes
            self.filesize = len(raw_bytes)
        else:
            return None
        # Let the user tell us whether or not the GCI is packed when importing
        # a file - this should help us tell the user not to do something that
        # might end up corrupting their data (or something to that effect).
        self.packed = packed

    ''' These functions return other types '''

    def blocksize(self):
        return struct.unpack(">h", self.raw_bytes[0x38:0x3a])[0]

    ''' These functions return raw bytes '''

    def dump(self):
        return self.raw_bytes
    def get_dentry(self):
        return self.raw_bytes[0:0x40]
    def get_game_id(self):
        return self.raw_bytes[0x00:0x04]
    def get_maker_code(self):
        return self.raw_bytes[0x04:0x06]
    def get_filename(self):
        return self.raw_bytes[0x08:0x28]
    def get_modtime(self):
        return self.raw_bytes[0x28:0x2c]
    def get_image_off(self):
        return self.raw_bytes[0x2c:0x30]
    def get_icon_fmt(self):
        return self.raw_bytes[0x30:0x32]
    def get_anim_speed(self):
        return self.raw_bytes[0x32:0x34]
    def get_permissions(self):
        return self.raw_bytes[0x34:0x35]
    def get_copy_ctr(self):
        return self.raw_bytes[0x35:0x36]
    def get_first_block(self):
        return self.raw_bytes[0x36:0x38]
    def get_block_count(self):
        return self.raw_bytes[0x38:0x3a]
    def get_comment_addr(self):
        return self.raw_bytes[0x3c:0x40]
    def set_filename(self, new_filename):
        self.raw_bytes[0x08:0x28] = new_filename
    def set_modtime(self, new_modtime):
        self.raw_bytes[0x28:0x2c] = struct.pack(">L", new_modtime)
    def set_block_count(self, new_bc):
        self.raw_bytes[0x38:0x3a] = new_bc
    def set_comment_addr(self, new_addr):
        self.raw_bytes[0x3c:0x40] = new_addr
    def set_permissions(self, new_perm):
        self.raw_bytes[0x34:0x35] = struct.pack(">B", new_perm)
    def _checksum(self, target_offset, count):
        """ Given some offset into raw_bytes and a count, compute checksum
            over the set of bytes in the GCI """

        # This is the seed for all checksum values
        new_checksum = bytearray( b'\x01\x23\x45\x67\x89\xAB\xCD\xEF' +
                                  b'\xFE\xDC\xBA\x98\x76\x54\x32\x10' )
        cur = 0
        cur_arr = 0
        arr_pos = 0
        x = 0
        y = 0
        ctr = (count) / 8
        while (ctr > 0):
            for i in range(0, 8):
                cur = self.raw_bytes[target_offset + i]
                cur_arr = new_checksum[(arr_pos & 0xf)]
                new_checksum[(arr_pos & 0xf)] = (cur + cur_arr) & 0xff
                arr_pos += 1
            ctr -= 1
            target_offset += 8
        for i in range(1, 0xf):
            x = new_checksum[i-1]
            y = new_checksum[i]
            if (x == y):
                x = y ^ 0x00FF
                new_checksum[i] = x
        return new_checksum

class melee_gamedata(melee_gci):
    ''' Class representing a plain-ol' Melee gamedata savefile (0x16040 bytes).
        The checksum/packing functions here are specific to the format,
        so you'll need another class for other types of save files. '''

    def get_raw_checksum(self, blknum):
        """ Return checksum bytes for some block 0-10 """
        base_offset = 0x2040
        if (blknum >= 0) and (blknum <= (self.blocksize()-1)):
            target_offset = base_offset + (blknum * 0x2000)
            return self.raw_bytes[target_offset:target_offset + 0x10]
        else:
            return None

    def set_raw_checksum(self, blknum, new_checksum):
        """ Given some blknum 0-10 and a 0x10-byte bytearray, replace the
            specified checksum bytes with the new bytes """
        base_offset = 0x2040
        if (blknum >= 0) and (blknum <= (self.blocksize() -1)):
            target_offset = base_offset + (blknum * 0x2000)
            self.raw_bytes[target_offset:target_offset + 0x10] = new_checksum
        else:
            raise Exception("Can't set checksum bytes for block {}".format(blknum))
            

    def checksum_block(self, blknum):
        """ Given some block number 0-10, compute the checksum for the
            associated data. Returns the raw checksum bytes. """
        base_offset = 0x2050
        data_size = 0x1ff0
        if (blknum >= 0) and (blknum <= (self.blocksize() - 1)):
            target_offset = base_offset + (blknum * 0x2000)
            return self._checksum(target_offset, data_size)
        else:
            raise Exception("Can't compute checksum bytes for block {}".format(blknum))
            

    def recompute_checksums(self):
        """ Recompute all checksum values and write them back """
        if (self.packed is True):
            raise Exception("You can only recompute checksums on unpacked data")
            

        # Retrieve checksum values for all blocks
        current = []
        for i in range(0, self.blocksize()-1):
            current.append(self.get_raw_checksum(i))

        # Compute checksum values for all blocks
        computed = []
        for i in range(0, self.blocksize()-1):
            computed.append(self.checksum_block(i))

        # If current checksums don't match, write them back
        for i in range(0, self.blocksize()-1):
            if (current[i] != computed[i]):
                log('DEBUG', "Block {} checksum mismatch, fixing ..".format(i))
                self.set_raw_checksum(i, computed[i])
            else:
                log('DEBUG', "Block {} checksum unchanged".format(i))

    def get_block(self, blknum):
        ''' Get the data portion of some block '''
        if (blknum > 10):
            return None
        base = 0x2000 * blknum + 0x2060
        return self.raw_bytes[base:(base + 0x1fe0)]

    def set_block(self, blknum, data):
        ''' Set the data on some block; takes a 0x1fe0-byte bytearray  '''
        if (blknum > 10):
            return None
        base = 0x2000 * blknum + 0x2060
        self.raw_bytes[base:(base + 0x1fe0)] = data

    def unpack(self):
        """ Unpack all blocks of data """
        if (self.packed is False):
            raise Exception("Data is already unpacked - refusing to unpack")
            
        log('DEBUG', "Unpacking GCI data")

        PREV_BYTE_OFFSET = 0x204f
        BASE_OFFSET = 0x2050
        DATA_SIZE = 0x1ff0
        for j in range(0, self.blocksize()-1):
            prev = self.raw_bytes[PREV_BYTE_OFFSET]
            for i in range(BASE_OFFSET, BASE_OFFSET + DATA_SIZE):
                cursor = self.raw_bytes[i]
                res = unpack(prev, cursor)
                self.raw_bytes[i] = res
                prev = cursor
            PREV_BYTE_OFFSET += 0x2000
            BASE_OFFSET += 0x2000
        if (self.packed is True):
            self.packed = False

    def pack(self):
        """ Pack all blocks of data """
        if (self.packed is True):
            raise Exception("Data is already packed -- refusing to pack")
            
        log('DEBUG', "Packing GCI data")

        PREV_BYTE_OFFSET = 0x204f
        BASE_OFFSET = 0x2050
        DATA_SIZE = 0x1ff0
        for j in range(0, self.blocksize()-1):
            prev = self.raw_bytes[PREV_BYTE_OFFSET]
            for i in range(BASE_OFFSET, BASE_OFFSET + DATA_SIZE):
                cursor = self.raw_bytes[i]
                res = pack(prev, cursor)
                self.raw_bytes[i] = res
                prev = res
            PREV_BYTE_OFFSET += 0x2000
            BASE_OFFSET += 0x2000
        if (self.packed is False):
            self.packed = True


class melee_snapshot(melee_gci):
    """ Class representing a snapshot file. """
    def get_raw_region_0_checksum(self):
        return self.raw_bytes[0x1e80:0x1e90]
    def get_raw_header_checksum(self):
        return self.raw_bytes[0x1eb0:0x1ec0]
    def get_raw_checksum(self, blknum):
        """ Return checksum bytes for some block 0-10 """
        base_offset = 0x2040
        if (blknum >= 0) and (blknum <= (self.blocksize()-1)):
            target_offset = base_offset + (blknum * 0x2000)
            return self.raw_bytes[target_offset:target_offset + 0x10]
        else:
            return None

    def set_raw_region_0_checksum(self, new_checksum):
        self.raw_bytes[0x1e80:0x1e90] = new_checksum
    def set_raw_header_checksum(self, new_checksum):
        self.raw_bytes[0x1eb0:0x1ec0] = new_checksum
    def set_raw_checksum(self, blknum, new_checksum):
        """ Given some blknum 0-10 and a 0x10-byte bytearray, replace the
            specified checksum bytes with the new bytes """
        base_offset = 0x2040
        if (blknum >= 0) and (blknum <= (self.blocksize() -1)):
            target_offset = base_offset + (blknum * 0x2000)
            self.raw_bytes[target_offset:target_offset + 0x10] = new_checksum
        else:
            raise Exception("Can't set checksum bytes for block {}".format(blknum))
            

    def checksum_region_0(self):
        """ Compute the header checksum """
        base_offset = 0x40
        data_size = 0x1e40
        return self._checksum(base_offset, data_size)
    def checksum_header(self):
        """ Compute the header checksum """
        base_offset = 0x1ec0
        data_size = 0x180
        return self._checksum(base_offset, data_size)
    def checksum_block(self, blknum):
        """ Given some block number 0-10, compute the checksum for the
            associated data. Returns the raw checksum bytes. """
        base_offset = 0x2050
        data_size = 0x1ff0
        if (blknum >= 0) and (blknum <= (self.blocksize() - 1)):
            target_offset = base_offset + (blknum * 0x2000)
            return self._checksum(target_offset, data_size)
        else:
            raise Exception("Can't compute checksum bytes for block {}".format(blknum))
            

    def recompute_checksums(self):
        """ Recompute all checksum values and write them back """
        if (self.packed is True):
            raise Exception("You can only recompute checksums on unpacked data")
            

        if (self.get_raw_header_checksum() != self.checksum_header()):
            log('DEBUG', "Header checksum mismatch, fixing ..")
            self.set_raw_header_checksum(self.checksum_header())
        else:
            log('DEBUG', "Header checksum unchanged")

        # Retrieve checksum values for all blocks
        current = []
        for i in range(0, self.blocksize()-1):
            current.append(self.get_raw_checksum(i))

        # Compute checksum values for all blocks
        computed = []
        for i in range(0, self.blocksize()-1):
            computed.append(self.checksum_block(i))

        # If current checksums don't match, write them back
        for i in range(0, self.blocksize()-1):
            if (current[i] != computed[i]):
                log('DEBUG', "Block {} checksum mismatch, fixing ..".format(i))
                self.set_raw_checksum(i, computed[i])
            else:
                log('DEBUG', "Block {} checksum unchanged".format(i))


    def unpack(self):
        """ Unpack all data """
        if (self.packed is False):
            raise Exception("Data is already unpacked - refusing to unpack")
            
        log('DEBUG', "Unpacking GCI data")

        # Unpack the data header region
        PREV_BYTE_OFFSET = 0x1ebf
        BASE_OFFSET = 0x1ec0
        DATA_SIZE = 0x180
        prev = self.raw_bytes[PREV_BYTE_OFFSET]
        for i in range(BASE_OFFSET, BASE_OFFSET + DATA_SIZE):
            cursor = self.raw_bytes[i]
            res = unpack(prev, cursor)
            self.raw_bytes[i] = res
            prev = cursor

        PREV_BYTE_OFFSET = 0x204f
        BASE_OFFSET = 0x2050
        DATA_SIZE = 0x1ff0
        for j in range(0, self.blocksize() - 1):
            prev = self.raw_bytes[PREV_BYTE_OFFSET]
            for i in range(BASE_OFFSET, BASE_OFFSET + DATA_SIZE):
                cursor = self.raw_bytes[i]
                res = unpack(prev, cursor)
                self.raw_bytes[i] = res
                prev = cursor
            PREV_BYTE_OFFSET += 0x2000
            BASE_OFFSET += 0x2000

        if (self.packed is True):
            self.packed = False


    def pack(self):
        """ Pack all blocks of data """
        if (self.packed is True):
            raise Exception("Data is already packed -- refusing to pack")
            
        log('DEBUG', "Packing GCI data")

        # Pack the data header region
        PREV_BYTE_OFFSET = 0x1ebf
        BASE_OFFSET = 0x1ec0
        DATA_SIZE = 0x180
        prev = self.raw_bytes[PREV_BYTE_OFFSET]
        for i in range(BASE_OFFSET, BASE_OFFSET + DATA_SIZE):
            cursor = self.raw_bytes[i]
            res = pack(prev, cursor)
            self.raw_bytes[i] = res
            prev = res

        PREV_BYTE_OFFSET = 0x204f
        BASE_OFFSET = 0x2050
        DATA_SIZE = 0x1ff0
        for j in range(0, self.blocksize()-1):
            prev = self.raw_bytes[PREV_BYTE_OFFSET]
            for i in range(BASE_OFFSET, BASE_OFFSET + DATA_SIZE):
                cursor = self.raw_bytes[i]
                res = pack(prev, cursor)
                self.raw_bytes[i] = res
                prev = res
            PREV_BYTE_OFFSET += 0x2000
            BASE_OFFSET += 0x2000
        if (self.packed is False):
            self.packed = True

