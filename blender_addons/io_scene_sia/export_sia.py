import bpy
from struct import pack
import bmesh
import ntpath
import os
import sys
from collections import OrderedDict


def write_string(file, string):
    file.write(pack('<I', len(string)))
    file.write(bytes(string, "utf8"))


class VertWithUV(object):
    def __init__(self, vert, uv):
        self.inner_vert = vert
        self.uv = uv


def save(context, filepath):
    print(filepath)
    with open(filepath, "wb") as file:
        me = bpy.context.object.data

        bm = bmesh.new()   # create an empty BMesh
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(me)
        me.calc_tangents()
        bm.from_mesh(me)

        bm.verts.index_update()
        bm.edges.index_update()
        bm.faces.index_update()

        min_x = sys.float_info.max
        min_y = sys.float_info.max
        min_z = sys.float_info.max

        max_x = sys.float_info.min
        max_y = sys.float_info.min
        max_z = sys.float_info.min

        uv_lay = bm.loops.layers.uv.active

        vertices = OrderedDict()
        for face in bm.faces:
            for loop in face.loops:
                vert = loop.vert
                vertices[vert.index] = VertWithUV(vert, loop[uv_lay].uv)

                min_x = min(min_x, vert.co.x)
                min_y = min(min_y, vert.co.y)
                min_z = min(min_z, vert.co.z)

                max_x = max(max_x, vert.co.x)
                max_y = max(max_y, vert.co.y)
                max_z = max(max_z, vert.co.z)

        for _, vert in sorted(vertices.items()):
            uv = vert.uv

        # return {'FINISHED'}

        file.write(b"SHSM")
        # Is this the version?
        file.write(pack('<I', 35))

        filename = os.path.splitext(ntpath.basename(filepath))[0]
        write_string(file, filename)

        # So far these bytes have only been zero
        file.write(bytearray(12))

        # This might be some sort of scale, since it tends to resemble another bounding box value
        # changing it did nothing
        file.write(pack('<f', max_x))

        # model.bounding_box.min_x
        file.write(pack('<f', min_x))
        # model.bounding_box.min_y
        file.write(pack('<f', min_y))
        # model.bounding_box.min_z
        file.write(pack('<f', min_z))

        # model.bounding_box.max_x
        file.write(pack('<f', max_x))
        # model.bounding_box.max_y
        file.write(pack('<f', max_y))
        # model.bounding_box.max_z
        file.write(pack('<f', max_z))

        # model.objects_num
        file.write(pack('<I', 1))

        # So far has been 0's, when I changed it the mesh became invisible
        file.write(bytearray(4))

        # num_vertices
        file.write(pack('<I', len(vertices)))

        # Zero's, changing it made it invisible
        file.write(bytearray(4))

        # This diveded by 3 gives the amount of faces, like another set of bytes later on
        # I'm wondering if this is the total amount of faces, and the other one is per mesh
        # model.something_about_faces_or_vertices
        file.write(pack('<I', len(bm.faces) * 3))
        file.write(bytearray(4))  # Unknown
        # Unknown
        file.write(bytearray([255, 255, 255, 255, 255, 255, 255, 255]))

        # This needs to be moved into the mesh, then maybe when reading faces/vertices/materials one can match against it.
        # model.object_id
        file.write(pack('<I', 1))

        # Changing these did nothing
        file.write(bytearray(16))

        # model.num_meshes
        # file.write(pack('<I', 1))

        # Changing these did nothing
        # file.write(bytearray(16))

        for _ in range(0, 1):  # 0, num_meshes
            write_string(file, "ball")  # material name
            # materials_num
            file.write(pack('<B', 1))
            for _ in range(0, 1):  # 0, materials_num
                # I should figure out why this is "base" maybe it needs to be
                write_string(file, "base")
                file.write(pack('<B', 4))  # textures num
                for _ in range(0, 1):  # 0, textures num
                    # Maybe a way to identify which texture it is, like a id
                    file.write(pack('<B', 0))
                    # texture path
                    write_string(file, "mesh/ball/white_ball_[al]")

                    file.write(pack('<B', 1))
                    # texture path
                    write_string(file, "mesh/ball/white_ball_[ro]_[me]_[ao]")

                    file.write(pack('<B', 2))
                    # texture path
                    write_string(file, "mesh/ball/white_ball_[no]")

                    file.write(pack('<B', 5))
                    # texture path
                    write_string(file, "mesh/ball/white_ball_[ma]")

        # Not sure what these are
        file.write(bytearray(24))
        file.write(bytearray(24))
        file.write(bytearray(16))

        # Maybe this is for this mesh, and the earlier one is for the entire file.
        # local_num_vertecies
        file.write(pack('<I', len(vertices)))

        # Seems to be important for the mesh to show up
        file.write(pack('<I', 39))

        for index, vert in sorted(vertices.items()):
            file.write(pack('<f', vert.inner_vert.co.x))
            file.write(pack('<f', vert.inner_vert.co.y))
            file.write(pack('<f', vert.inner_vert.co.z))

            # Unsure if these are normals or not
            # I should find a simple object, like a flat plane and check to see
            # where the normals are, or whatever it might be
            # From checking again, I'm confident these are the normals, don't know what the others are.
            # file.write(bytearray(12))
            file.write(pack('<f', vert.inner_vert.normal.x))
            file.write(pack('<f', vert.inner_vert.normal.y))
            file.write(pack('<f', vert.inner_vert.normal.z))

            uv = vert.uv
            file.write(pack('<f', uv.x))
            file.write(pack('<f', uv.y))

            # Changed these, did nothing
            # Adding them did add shading to the mesh ingame
            # print(vert.inner_vert.tangent)
            # file.write(pack('<f', 10))
            # file.write(bytearray(8))
            # file.write(pack('<f', 0))
            # file.write(pack('<f', 0))
            # Last one is usually 1 or -1
            # file.write(pack('<f', 0))
            file.write(bytearray(16))

        # number of entries, so the triangle amount * 3
        file.write(pack('<I', len(bm.faces) * 3))
        for face in bm.faces:
            for loop in face.loops:
                vert = loop.vert
                file.write(pack('<H', vert.index))

        file.write(bytearray(13))

        file.write(b"EHSM")
        bm.free()
        return {'FINISHED'}

    return {'CANCELED'}
