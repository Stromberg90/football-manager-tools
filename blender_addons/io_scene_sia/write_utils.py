from struct import pack

def u32(file, n):
    file.write(pack('<I', n))


def u16(file, n):
    file.write(pack('<H', n))


def u8(file, n):
    file.write(pack('<B', n))


def f32(file, n):
    file.write(pack('<f', n))


def string(file, str):
    u32(file, len(str.encode('utf-8')))
    file.write(bytes(str, 'utf-8'))


def string_without_len(file, str):
    file.write(bytes(str, 'utf-8'))


def string_u8(file, str):
    u8(file, len(str.encode('utf-8')))
    file.write(bytes(str, 'utf-8'))


def vector3(file, vec):
    f32(file, vec.x)
    f32(file, vec.y)
    f32(file, vec.z)


def vector2(file, vec):
    f32(file, vec.x)
    f32(file, vec.y)


def zeros(file, n):
    file.write(bytearray(n))


def full_bytes(file, n):
    for _ in range(0, n):
        u8(file, 255)
