from io import BufferedWriter
from typing import Any
import bpy
from mathutils import Matrix
from struct import pack
import bmesh
import ntpath
import os
import sys
from collections import OrderedDict
from bpy_extras.io_utils import (
    orientation_helper,
    axis_conversion,
)
import pprint
from . import data_types
from . import write_utils


def triangulate(me):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()


def save(context: Any, filepath="", axis_forward='Y', axis_up='Z', use_selection=False):
    def rvec3d(v):
        return round(v[0], 6), round(v[1], 6), round(v[2], 6)

    def rvec2d(v):
        return round(v[0], 6), round(v[1], 6)

    with open(filepath, "wb") as file:
        # TODO: Setting for configuring the base path like: C:\Users\%USER%\Documents\Sports Interactive\Football Manager 2021
        # then on export it would cut away that part of the path to make relative filepaths.
        scene = context.scene
        if use_selection:
            context_objects = context.selected_objects
        else:
            context_objects = context.view_layer.objects
        if use_selection:
            data_seq = context.selected_objects
        else:
            data_seq = scene.objects

        global_matrix = axis_conversion(
            to_forward=axis_forward,
            to_up=axis_up,
        ).to_4x4() @ Matrix.Scale(1.0, 4)

        model = data_types.Model()
        model.bounding_box = data_types.BoundingBox()
        model.name = os.path.splitext(os.path.basename(filepath))[0]

        for mesh_index, obj in enumerate(context_objects):
            sia_mesh = data_types.Mesh()

            if obj.mode == "EDIT":
                obj.update_from_editmode()

            depsgraph = bpy.context.evaluated_depsgraph_get()
            mesh_owner = obj.evaluated_get(depsgraph)

            mesh = mesh_owner.to_mesh()

            if mesh is None:
                return

            triangulate(mesh)

            mat = global_matrix @ obj.matrix_world
            mesh.transform(mat)
            if mat.is_negative:
                mesh.flip_normals()

            mesh.calc_normals_split()

            active_uv_layer = mesh.uv_layers.active.data

            materials = mesh.materials[:]
            for material in materials:
                sia_material = data_types.Material()
                sia_material.name = material.name
                sia_material.kind = "base"
                for texture in [("stadiums/textures/no_stand/empty_corner_concrete_02_[al]", 0), ("stadiums/textures/no_stand/empty_corner_concrete_02_[ro]_[me]_[ao]", 1), ("stadiums/textures/no_stand/empty_corner_concrete_02_[no]", 2), ("stadiums/textures/no_stand/empty_corner_concrete_02_[ma]", 5)]:
                    sia_texture = data_types.Texture()
                    sia_texture.name = texture[0]
                    sia_texture.id = texture[1]
                    sia_material.textures.append(sia_texture)

                sia_mesh.materials.append(sia_material)

            sia_mesh.id = mesh_index

            mesh_verts = mesh.vertices
            vdict = [{} for i in range(len(mesh_verts))]
            ply_verts = []
            ply_faces = [[] for f in range(len(mesh.polygons))]
            vert_count = 0

            for i, f in enumerate(mesh.polygons):
                uv = [active_uv_layer[l].uv[:]
                    for l in range(f.loop_start, f.loop_start + f.loop_total)
                ]
                pf = ply_faces[i]
                for j, vidx in enumerate(f.vertices):
                    v = mesh_verts[vidx]

                    normal = v.normal[:]
                    normal_key = rvec3d(normal)

                    uvcoord = uv[j][0], ((uv[j][1] * - 1) + 1)
                    uvcoord_key = rvec2d(uvcoord)

                    key = normal_key, uvcoord_key

                    vdict_local = vdict[vidx]
                    pf_vidx = vdict_local.get(key)

                    if pf_vidx is None:  # Same as vdict_local.has_key(key)
                        pf_vidx = vdict_local[key] = vert_count
                        ply_verts.append((vidx, normal, uvcoord))
                        vert_count += 1

                    pf.append(pf_vidx)

            # TODO: Move this inline into the loop above
            for index, normal, uv_coords in ply_verts:
                vertex = data_types.Vertex()
                vert = mesh_verts[index]
                vertex.position = data_types.Vector3(vert.co.x, vert.co.y, vert.co.z)
                vertex.normal = data_types.Vector3(normal[0], normal[1], normal[2])
                vertex.uv = data_types.Vector2(uv_coords[0], uv_coords[1])
                model.bounding_box.update_with_vector(vertex.position)
                sia_mesh.vertices.append(vertex)

            # TODO: Move this inline into the loop above
            for pf in ply_faces:
                triangle = data_types.Triangle()
                triangle.index1 = pf[0]
                triangle.index2 = pf[1]
                triangle.index3 = pf[2]
                sia_mesh.triangles.append(triangle)

            # TODO: These don't need to be fields, it can compute this when writing it.
            sia_mesh.vertices_num = len(sia_mesh.vertices)
            sia_mesh.triangles_num = len(sia_mesh.triangles)

            model.meshes[mesh_index] = sia_mesh

            mesh_owner.to_mesh_clear()

        file.write(b"SHSM")

        file.write(pack('<I', 35))

        write_utils.write_string(file, model.name)

        write_utils.write_zeros(file, 12)

        write_utils.write_f32(file, max(model.bounding_box.max_x, max(model.bounding_box.max_y, model.bounding_box.max_z)))

        write_utils.write_f32(file, model.bounding_box.min_x)
        write_utils.write_f32(file, model.bounding_box.min_y)
        write_utils.write_f32(file, model.bounding_box.min_z)

        write_utils.write_f32(file, model.bounding_box.max_x)
        write_utils.write_f32(file, model.bounding_box.max_y)
        write_utils.write_f32(file, model.bounding_box.max_z)

        write_utils.write_u32(file, len(model.meshes))

        for (mesh_id, mesh) in model.meshes.items():
            write_utils.write_zeros(file, 4)
            write_utils.write_u32(file, mesh.vertices_num)

            write_utils.write_zeros(file, 4)
            write_utils.write_u32(file, mesh.triangles_num * 3)

            write_utils.write_u32(file, mesh_id)
            write_utils.write_u8(file, 255) # Did not see any difference when setting it to 0
            write_utils.write_u8(file, 255) # Did not see any difference when setting it to 0
            write_utils.write_u8(file, 255) # Did not see any difference when setting it to 0
            write_utils.write_u8(file, 255) # Setting it to zero made it crash
            write_utils.write_u8(file, 255) # Did not see any difference when setting it to 0
            write_utils.write_u8(file, 255) # Did not see any difference when setting it to 0
            write_utils.write_u8(file, 255) # Did not see any difference when setting it to 0
            write_utils.write_u8(file, 255) # Setting it to zero made it crash
            # for _ in range(0, 8):
            #     write_utils.write_u8(file, 255)

        write_utils.write_u32(file, len(model.meshes))

        write_utils.write_zeros(file, 16)

        # TODO: When exporting I want to split the materials on a mesh into their
        # own mesh and export that, unless I can do multiple materials without it?
        # since I want to do different tileable materials and such.
        # like, is there any data when I read/write the faces which could be the material index?
        for (mesh_id, mesh) in model.meshes.items():
            write_utils.write_string(file, mesh.materials[0].name)
            write_utils.write_u8(file, len(mesh.materials))
            for material in mesh.materials:
                write_utils.write_string(file, material.kind)
                write_utils.write_u8(file, len(material.textures))
                for texture in material.textures:
                    write_utils.write_u8(file, texture.id)
                    write_utils.write_string(file, texture.name)

            if mesh_id != len(model.meshes) - 1:
                write_utils.write_zeros(file, 80)

        write_utils.write_zeros(file, 64)

        vertices_total_num = 0
        number_of_triangles = 0
        for (mesh_id, mesh) in model.meshes.items():
            vertices_total_num += mesh.vertices_num
            number_of_triangles += mesh.triangles_num

        write_utils.write_u32(file, vertices_total_num)

        model.settings = data_types.Bitfield()
        model.settings[0] = True
        model.settings[1] = True
        model.settings[2] = True
        write_utils.write_u32(file, model.settings.number())

        for (mesh_id, mesh) in model.meshes.items():
            for vertex in mesh.vertices:
                if model.settings[0]:
                    write_utils.write_vector3(file, vertex.position)
                if model.settings[1]:
                    write_utils.write_vector3(file, vertex.normal)
                if model.settings[2]:
                    write_utils.write_vector2(file, vertex.uv)

        write_utils.write_u32(file, number_of_triangles * 3)

        for (mesh_id, mesh) in model.meshes.items():
            for triangle in mesh.triangles:
                if vertices_total_num > 65535:
                    write_utils.write_triangle_u32(file, triangle)
                else:
                    write_utils.write_triangle_u16(file, triangle)

        write_utils.write_u32(file, 0)  # some_number
        write_utils.write_u32(file, 0)  # some_number2

        write_utils.write_u8(file, 0)  # num

        write_utils.write_u32(file, 0)  # instances

        file.write(b"EHSM")

        return {'FINISHED'}

    return {'CANCELED'}
