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

def write_vector3(file, vec):
    write_f32(file, vec.x)
    write_f32(file, vec.y)
    write_f32(file, vec.z)

def write_vector2(file, vec):
    write_f32(file, vec.x)
    write_f32(file, vec.y)


def write_triangle_u32(file, triangle):
    write_u32(file, triangle.index1)
    write_u32(file, triangle.index2)
    write_u32(file, triangle.index3)


def write_triangle_u16(file, triangle):
    write_u16(file, triangle.index1)
    write_u16(file, triangle.index2)
    write_u16(file, triangle.index3)


def write_zeros(file, n):
    file.write(bytearray(n))
