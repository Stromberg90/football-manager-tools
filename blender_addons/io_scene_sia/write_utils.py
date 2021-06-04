from struct import pack

def write_u32(file, n):
    file.write(pack('<I', n))


def write_u16(file, n):
    file.write(pack('<H', n))


def write_u8(file, n):
    file.write(pack('<B', n))


def write_f32(file, n):
    file.write(pack('<f', n))


def write_string(file, str):
    write_u32(file, len(str.encode('utf-8')))
    file.write(bytes(str, 'utf-8'))


def write_string_without_len(file, str):
    file.write(bytes(str, 'utf-8'))


def write_string_u8(file, str):
    write_u8(file, len(str.encode('utf-8')))
    file.write(bytes(str, 'utf-8'))
