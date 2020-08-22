import bpy
from struct import unpack
import bmesh
import ntpath
import os
import sys
from collections import OrderedDict


def read_string(file):
    length = unpack('<I', file.read(4))[0]
    return str(file.read(length), "utf-8")


def read_u32(file):
    return unpack('<I', file.read(4))[0]


def read_u16(file):
    return unpack('<H', file.read(2))[0]


def read_f32(file):
    return unpack('<f', file.read(4))[0]


def load(context, filepath):
    sia_file = open(filepath, 'rb')
    if sia_file.read(4) != b'SHSM':
        print("Not a valid file")
        return {'CANCELED'}

    maybe_version = read_u32(sia_file)
    filename = read_string(sia_file)
    print("filename: ", filename)

    print(sia_file.read(12))

    print(read_f32(sia_file))

    min_x = read_f32(sia_file)
    min_y = read_f32(sia_file)
    min_z = read_f32(sia_file)

    max_x = read_f32(sia_file)
    max_y = read_f32(sia_file)
    max_z = read_f32(sia_file)

    print("min_x: ", min_x)
    print("min_y: ", min_y)
    print("min_z: ", min_z)

    print("max_x: ", max_x)
    print("max_y: ", max_y)
    print("max_z: ", max_z)

    objects_num = read_u32(sia_file)
    print("objects_num: ", objects_num)

    print(sia_file.read(4))

    num_vertices = read_u32(sia_file)
    print("num_vertices: ", num_vertices)

    print(sia_file.read(4))

    num_faces = int(read_u32(sia_file) / 3)
    print("num_faces: ", num_faces)
    print(sia_file.read(4))
    print(sia_file.read(8))

    maybe_id = read_u32(sia_file)
    print("maybe_id: ", maybe_id)

    print(sia_file.read(16))

    for _ in range(0, 1):
        material_name = read_string(sia_file)
        print(material_name)
        materials_num = unpack('<B', sia_file.read(1))[0]
        print("materials_num: ", materials_num)
        for _ in range(0, materials_num):
            print(read_string(sia_file))
            textures_num = unpack('<B', sia_file.read(1))[0]
            print("textures_num: ", textures_num)
            for _ in range(0, textures_num):
                print(unpack('<B', sia_file.read(1))[0])
                print(read_string(sia_file))

    print(sia_file.read(24))
    print(sia_file.read(24))
    print(sia_file.read(16))

    maybe_this_meshes_vertices = read_u32(sia_file)
    print("maybe_this_meshes_vertices: ", maybe_this_meshes_vertices)

    print(read_u32(sia_file))

    return {'FINISHED'}
    for _ in range(0, num_vertices):
        print("Vec X: %.2f" % read_f32(sia_file))
        print("Vec Y: %.2f" % read_f32(sia_file))
        print("Vec Z: %.2f" % read_f32(sia_file))

        print("Norm X: %.2f" % read_f32(sia_file))
        print("Norm Y: %.2f" % read_f32(sia_file))
        print("Norm Z: %.2f" % read_f32(sia_file))

        print("UV X: %.2f" % read_f32(sia_file))
        print("UV Y: %.2f" % read_f32(sia_file))

        print(sia_file.read(16))

    for _ in range(0, num_faces * 3):
        print("Face Index: ", read_u16(sia_file))

    print(sia_file.read(13))

    print(sia_file.read(4))

    sia_file.close()
    return {'FINISHED'}
