"""mem2gci.py: Translates Melee memory addresses to their corresponding location in an unpacked GCI, and vice-versa."""

from typing import List, Tuple

BLOCK_LIST = [          #GCI block offset list
        0x02060,        #Block 0
        0x04060,        #Block 1
        0x06060,        #Block 2
        0x08060,        #Block 3
        0x0a060,        #Block 4
        0x0c060,        #Block 5
        0x0e060,        #Block 6
        0x10060,        #Block 7
        0x12060,        #Block 8
        0x14060,        #Block 9
        ]

MEM_LIST = [            #Melee start address for each GCI block
        0x00000000,     #Block 0 (not in memory)
        0x8045d6b8,     #Block 1
        0x8045f5e4,     #Block 2
        0x80461510,     #Block 3
        0x8046343c,     #Block 4
        0x80465368,     #Block 5
        0x80467294,     #Block 6
        0x804691c0,     #Block 7
        0x00000000,     #Block 8 (not in memory)
        0x8045bf28,     #Block 9
        ]

BLOCK_SIZE = [0, 0x1f2c, 0x1f2c, 0x1f2c, 0x1f2c, 0x1f2c, 0x1f2c, 0x1f2c, 0, 0x1790]
BLOCK_START = BLOCK_LIST[0]
BLOCK_END = BLOCK_LIST[9] + BLOCK_SIZE[9]
MEM_START = MEM_LIST[9] # Memory starts with block 9 for some reason
MEM_END = MEM_LIST[7] + BLOCK_SIZE[7]

def mem2gci_tuple(mem_address: int) -> Tuple[int, int]:
    """Takes a Melee memory address and returns the corresponding unpacked GCI
       block number and offset."""
    if mem_address < MEM_START or mem_address >= MEM_END:
        raise ValueError("Melee address 0x%08x does not have a corresponding GCI location" % mem_address)
    block_number = -1
    offset = 0
    for index, block_address in enumerate(MEM_LIST):
        offset = mem_address - block_address
        if offset >= BLOCK_SIZE[index] or offset < 0: continue
        block_number = index
        break
    if block_number < 0:
        raise ValueError("Melee address 0x%08x does not have a corresponding GCI location" % mem_address)
    return block_number, offset

def mem2gci(mem_address: int) -> int:
    """Takes a Melee memory address and returns the corresponding unpacked GCI
    location."""
    block_number, offset = mem2gci_tuple(mem_address)
    return BLOCK_LIST[block_number] + offset

def gci2mem(gci_address: int) -> int:
    """Takes a GCI offset address and returns the corresponding Melee memory
       location."""
    if gci_address < BLOCK_START or gci_address >= BLOCK_END:
        raise ValueError("GCI address 0x%05x does not have a corresponding Melee memory location" % gci_address)
    block_number = -1
    offset = 0
    for index, block_address in enumerate(BLOCK_LIST):
        offset = gci_address - block_address
        if offset >= BLOCK_SIZE[index] or offset < 0: continue
        block_number = index
        break
    if block_number < 0:
        raise ValueError("GCI address 0x%05x does not have a corresponding Melee memory location" % gci_address)
    return MEM_LIST[block_number] + offset

def data2gci(mem_start_address: int, data_length: int) -> List[Tuple[int, int]]:
    """Returns a list of GCI offsets and data lengths that directly correspond
       to the specified Melee memory address and data length. The data at these
       GCI offsets, in order, will load into Melee as a contiguous data block
       at the specified address."""
    if data_length <= 0:
        raise ValueError("Data length must be greater than 0.")
    if mem_start_address < MEM_START:
        raise ValueError("Start address 0x%08x is not present in the GCI; earliest possible start address is 0x%08x" % (mem_start_address, MEM_START))
    if mem_start_address + data_length > MEM_END:
        raise ValueError("Data ends at 0x%08x which overflows the last address present in the GCI (0x%08x)" % (mem_start_address + data_length, MEM_END))
    current_address = mem_start_address
    remaining_data = data_length
    gci_list: List[Tuple[int, int]] = []
    while remaining_data > 0:
        current_block_number, current_offset = mem2gci_tuple(current_address)
        current_gci_address = BLOCK_LIST[current_block_number] + current_offset
        amount_block_can_fit = BLOCK_SIZE[current_block_number] - current_offset
        gci_list.append((current_gci_address, min(remaining_data, amount_block_can_fit)))
        remaining_data -= amount_block_can_fit
        current_address += amount_block_can_fit
    return gci_list

