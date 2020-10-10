import bpy
from struct import unpack
import bmesh
import ntpath
import os
import sys
from collections import OrderedDict
from . import sia_parser


def load(context, filepath):
    model = sia_parser.load_file(filepath)

    print("Name: ", model.name)
    print("Mesh:")
    for mesh in model.meshes:
        print("  ID: ", mesh.id)
        print("  Materials: ")
        for material in mesh.materials:
            print("    Name: ", material.name)
            print("    Type: ", material.kind)
            print("    Textures:")
            for texture in material.textures:
                print("      Name: ", texture.name)
                print("      Type: ", texture.id)
            print("    Vertices: ")
        for vertex in mesh.vertices:
            print("      Vertex: ")
            print("        Position: X: ",
                  vertex.position[0], " Y: ", vertex.position[1], " Z: ", vertex.position[2])
            print("        UV: X: ", vertex.uv[0], " Y: ", vertex.uv[1])
            print("        Normals: X: ",
                  vertex.normals[0], " Y: ", vertex.normals[1], " Z: ", vertex.normals[2])
    return {'FINISHED'}
