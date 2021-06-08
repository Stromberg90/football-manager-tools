from struct import unpack
from io import BufferedReader

def skip(file: BufferedReader, offset: int) -> None:
    file.seek(offset, 1)


def u32(file: BufferedReader) -> int:
    return unpack('<I', file.read(4))[0]


def u16(file: BufferedReader) -> int:
    return unpack('<H', file.read(2))[0]


def u8(file: BufferedReader) -> int:
    return unpack('<B', file.read(1))[0]


def f32(file: BufferedReader) -> float:
    return unpack('<f', file.read(4))[0]


def string(file: BufferedReader) -> str:
    length = u32(file)
    if length == 0:
        return ""
    return unpack('<{}s'.format(length), file.read(length))[0]


def string_with_length(file: BufferedReader, length: int) -> str:
    return unpack('<{}s'.format(length), file.read(length))[0]


def string_u8_len(file: BufferedReader) -> str:
    length = u8(file)
    if length == 0:
        return ""    
    return unpack('<{}s'.format(length), file.read(length))[0]
