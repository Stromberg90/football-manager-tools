from io import BufferedWriter
from struct import pack

def write_u32(file: BufferedWriter, n: int):
    file.write(pack('<I', n))


def write_u16(file: BufferedWriter) -> int:    
    return unpack('<H', file.read(2))[0]


def write_u8(file: BufferedWriter) -> int:
    return unpack('<B', file.read(1))[0]


def write_f32(file: BufferedWriter) -> float:
    return unpack('<f', file.read(4))[0]


def write_string_len_then_string(file: BufferedWriter) -> str:
    length = write_u32(file)
    if length == 0:
        return ""
    return unpack('<{}s'.format(length), file.read(length))[0]


def write_string_without_len(file: BufferedWriter, length: int) -> str:
    return unpack('<{}s'.format(length), file.read(length))[0]


def write_string_u8_len_then_string(file: BufferedWriter) -> str:
    length = read_u8(file)
    if length == 0:
        return ""    
    return unpack('<{}s'.format(length), file.read(length))[0]
