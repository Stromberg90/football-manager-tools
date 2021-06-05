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
            b_mesh = bmesh.new()
            b_mesh.from_mesh(mesh)

            b_mesh.verts.index_update()
            b_mesh.edges.index_update()
            b_mesh.faces.index_update()

            # uv_lay = b_mesh.loops.layers.uv.active
            uv_layer = mesh.uv_layers.active.data[:]

            materials = mesh.materials[:]
            for material in materials:
                sia_material = data_types.Material()
                sia_material.name = material.name
                sia_mesh.materials.append(sia_material)

            sia_mesh.id = mesh_index

            # for face in b_mesh.faces:
            #     triangle = data_types.Triangle()
            #     triangle.index1 = face.verts[0].index
            #     triangle.index2 = face.verts[1].index
            #     triangle.index3 = face.verts[2].index
            #     sia_mesh.triangles.append(triangle)
            #     for loop in face.loops:
            #         vert = loop.vert
            #         vertex = data_types.Vertex()
            #         vertex.position = data_types.Vector3(vert.co.x, vert.co.y, vert.co.z)
            #         model.bounding_box.update_with_vector(vertex.position)
            #         vertex.normal = data_types.Vector3(vert.normal.x, vert.normal.y, vert.normal.z)
            #         uv = loop[uv_lay].uv
            #         vertex.uv = data_types.Vector2(uv.x, uv.y)
            #         sia_mesh.vertices.append(vertex)

            for v in mesh.vertices:
                vertex = data_types.Vertex()
                vertex.position = data_types.Vector3(v.co.x, v.co.y, v.co.z)
                model.bounding_box.update_with_vector(vertex.position)
                vertex.normal = data_types.Vector3(v.normal.x, v.normal.y, v.normal.z)
                uv = uv_layer[v.index].uv
                vertex.uv = data_types.Vector2(uv.x, uv.y)
                sia_mesh.vertices.append(vertex)

                # print("Index: ", v.index)
                # print("UV: ", uv_layer[v.index].uv)
                # print("Normal: ", v.normal)

            for triangle in mesh.polygons:
                indecies = triangle.vertices[:]
                triangle = data_types.Triangle()
                triangle.index1 = indecies[0]
                triangle.index2 = indecies[1]
                triangle.index3 = indecies[2]
                sia_mesh.triangles.append(triangle)

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
            write_utils.write_zeros(file, 8)

        write_utils.write_u32(file, len(model.meshes))

        write_utils.write_zeros(file, 16)

        # TODO: When exporting I want to split the materials on a mesh into their
        # own mesh and export that, unless I can do multiple materials without it?
        # since I want to do different tileable materials and such.
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

        print("Before writing vertices: ", file.tell())
        writes = 0
        for (mesh_id, mesh) in model.meshes.items():
            print("mesh.vertices: ", len(mesh.vertices))
            for vertex in mesh.vertices:
                print("VERT")
                if model.settings[0]:
                    write_utils.write_vector3(file, vertex.position)
                    writes += 3
                if model.settings[1]:
                    write_utils.write_vector3(file, vertex.normal)
                    writes += 3
                if model.settings[2]:
                    write_utils.write_vector2(file, vertex.uv)
                    writes += 2
            print("writes: ", writes)

        write_utils.write_u32(file, number_of_triangles * 3)
        print("number_of_triangles: ", number_of_triangles)
        print("number_of_triangles * 3: ", number_of_triangles * 3)

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
