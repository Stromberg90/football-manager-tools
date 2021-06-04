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

            uv_layer = mesh.uv_layers.active.data[:]
            mesh_verts = mesh.vertices[:]

            face_index_pairs = [(face, index) for index, face in enumerate(mesh.polygons)]
            for f in face_index_pairs:
                print(f)

            loops = mesh.loops

            materials = mesh.materials[:]
            material_names = [m.name if m else None for m in materials]
            print(material_names)
            print(len(face_index_pairs))

            mesh.calc_normals_split()

            sia_mesh = data_types.Mesh()
            sia_mesh.id = mesh_index
            sia_mesh.vertices_num = len(mesh_verts)
            sia_mesh.triangles_num = len(face_index_pairs)
            for (face, index) in face_index_pairs:
                indecies = [i for i in face.loop_indices]
                triangle = data_types.Triangle()
                triangle.index1 = indecies[0]
                triangle.index2 = indecies[1]
                triangle.index3 = indecies[2]
                sia_mesh.triangles.append(triangle)
                for vi in face.vertices:
                    v = mesh_verts[vi]
                    vertex = data_types.Vertex()
                    vertex.position = data_types.Vector3(v.co.x, v.co.y, v.co.z)
                    model.bounding_box.update_with_vector(vertex.position)

                    vertex.normal = data_types.Vector3(v.normal.x, v.normal.y, v.normal.z)
                    uv = uv_layer[v.index].uv
                    vertex.uv = data_types.Vector2(uv.x, uv.y)
                    sia_mesh.vertices.append(vertex)

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
        
        return {'FINISHED'}

    return {'CANCELED'}

