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
from . import utils


def texture_relative_path(node, addon_preferences):
    texture_path = node.image.filepath_from_user()

    basename = os.path.basename(texture_path)
    ext = os.path.splitext(basename)[1]

    if ext != ".dds":
        raise Exception("{} is not a dds file".format(basename))

    is_extracted_texture = texture_path.startswith(
        os.path.abspath(addon_preferences.base_extracted_textures_path) + os.sep
    )
    is_exported_texture = texture_path.startswith(
        os.path.abspath(addon_preferences.base_textures_path) + os.sep
    )

    if not is_exported_texture and not is_extracted_texture:
        raise Exception(
            "{} is not in any of the texture folders, check that it's set to the correct folder in the addon preferences".format(
                texture_path
            )
        )

    relative_path = None
    if is_exported_texture:
        relative_path = os.path.splitext(
            utils.asset_path(texture_path, addon_preferences.base_textures_path)
        )[0]
    elif is_extracted_texture:
        relative_path = os.path.splitext(
            utils.asset_path(
                texture_path,
                addon_preferences.base_extracted_textures_path,
            )
        )[0]

    return relative_path


def triangulate(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()


def save(
    context,
    filepath,
    addon_preferences,
    axis_forward="Y",
    axis_up="Z",
    use_selection=False,
):
    if use_selection:
        context_objects = context.selected_objects
    else:
        context_objects = context.view_layer.objects

    global_matrix = axis_conversion(
        to_forward=axis_forward,
        to_up=axis_up,
    ).to_4x4() @ Matrix.Scale(1.0, 4)

    model = data_types.Model()
    model.bounding_box = data_types.BoundingBox()
    model.name = os.path.splitext(os.path.basename(filepath))[0]

    valid_objects = []
    uses_lightmap = False

    for obj in context_objects:
        if obj.type not in ["MESH", "CURVE"]:
            continue

        if obj.mode == "EDIT":
            obj.update_from_editmode()

        depsgraph = bpy.context.evaluated_depsgraph_get()
        mesh_owner = obj.evaluated_get(depsgraph)

        try:
            mesh_owner.to_mesh()
        except RuntimeError:
            continue

        valid_objects.append(obj)

    for mesh_index, obj in enumerate(valid_objects):
        sia_mesh = data_types.Mesh()

        if obj.mode == "EDIT":
            obj.update_from_editmode()

        depsgraph = bpy.context.evaluated_depsgraph_get()
        mesh_owner = obj.evaluated_get(depsgraph)

        mesh = mesh_owner.to_mesh()

        triangulate(mesh)

        mat = global_matrix @ obj.matrix_world
        mesh.transform(mat)
        if mat.is_negative:
            mesh.flip_normals()

        # Since this is slow, it only needs to do this if export tangent is checked.
        mesh.calc_tangents()

        sia_mesh.id = mesh_index

        mesh_verts = mesh.vertices
        vdict = [{} for i in range(len(mesh_verts))]
        ply_verts = []
        ply_faces = [[] for f in range(len(mesh.polygons))]
        vert_count = 0
        used_material_indecies = []

        for i, f in enumerate(mesh.polygons):
            if f.material_index not in used_material_indecies:
                used_material_indecies.append(f.material_index)
            # by checking material_index on f, I'll be able to
            # split materials into their own meshes.
            uv = []
            for uv_layer in mesh.uv_layers:
                uv.append(
                    [
                        uv_layer.uv[loop].vector[:]
                        for loop in range(f.loop_start, f.loop_start + f.loop_total)
                    ]
                )
            pf = ply_faces[i]
            normals = []
            tangents = []

            for li in f.loop_indices:
                normals.append(mesh.loops[li].normal[:])
                tangents.append(mesh.loops[li].tangent[:])

            for j, vidx in enumerate(f.vertices):
                normal = normals[j]
                tangent = tangents[j]
                uvcoords = []
                for uv_point in uv:
                    uvcoords.append((uv_point[j][0], (uv_point[j][1] * -1) + 1))

                key = normal, uvcoords[0]

                vdict_local = vdict[vidx]
                pf_vidx = vdict_local.get(key)

                if pf_vidx is None:
                    pf_vidx = vdict_local[key] = vert_count
                    ply_verts.append((vidx, normal, uvcoords, tangent))
                    vert_count += 1

                pf.append(pf_vidx)

        materials = [
            mat
            for (index, mat) in enumerate(mesh.materials)
            if index in used_material_indecies
        ]

        for material in materials:
            node_tree = material.node_tree
            texture_map = {}
            for node in node_tree.nodes:
                if node.bl_idname == "ShaderNodeOutputMaterial":
                    surface_input = node.inputs["Surface"]
                    if surface_input:
                        if len(surface_input.links) > 0:
                            input = surface_input.links[0].from_node
                            if input.bl_idname == "ShaderNodeGroup":
                                if input.node_tree.name.startswith("FM Material"):
                                    fm_material = input
                                    albedo = fm_material.inputs["Albedo"]
                                    ro_me_ao = fm_material.inputs[
                                        "Roughness Metallic AO"
                                    ]
                                    normal = fm_material.inputs["Normal"]
                                    mask = fm_material.inputs["Mask"]
                                    lightmap = fm_material.inputs["Lightmap"]

                                    if len(albedo.links) > 0:
                                        input_node = albedo.links[0].from_node
                                        if input_node.bl_idname == "ShaderNodeTexImage":
                                            relative_path = texture_relative_path(
                                                input_node, addon_preferences
                                            )
                                            if relative_path:
                                                texture_map[
                                                    data_types.TextureKind.Albedo
                                                ] = relative_path
                                    if len(ro_me_ao.links) > 0:
                                        input_node = ro_me_ao.links[0].from_node
                                        if input_node.bl_idname == "ShaderNodeTexImage":
                                            relative_path = texture_relative_path(
                                                input_node, addon_preferences
                                            )
                                            if relative_path:
                                                texture_map[
                                                    data_types.TextureKind.RoughnessMetallicAmbientOcclusion
                                                ] = relative_path
                                    if len(normal.links) > 0:
                                        input_node = normal.links[0].from_node
                                        if input_node.bl_idname == "ShaderNodeTexImage":
                                            relative_path = texture_relative_path(
                                                input_node, addon_preferences
                                            )
                                            if relative_path:
                                                texture_map[
                                                    data_types.TextureKind.Normal
                                                ] = relative_path
                                    if len(mask.links) > 0:
                                        input_node = mask.links[0].from_node
                                        if input_node.bl_idname == "ShaderNodeTexImage":
                                            relative_path = texture_relative_path(
                                                input_node, addon_preferences
                                            )
                                            if relative_path:
                                                texture_map[
                                                    data_types.TextureKind.Mask
                                                ] = relative_path
                                    if len(lightmap.links) > 0:
                                        input_node = lightmap.links[0].from_node
                                        if input_node.bl_idname == "ShaderNodeTexImage":
                                            relative_path = texture_relative_path(
                                                input_node, addon_preferences
                                            )
                                            if relative_path:
                                                uses_lightmap = True
                                                texture_map[
                                                    data_types.TextureKind.Lightmap
                                                ] = relative_path

            sia_material = data_types.Material()
            sia_material.name = material.name
            # sia_material.kind = "base"
            sia_material.kind = "match_ball"
            for kind, path in texture_map.items():
                sia_texture = data_types.Texture()
                sia_texture.path = path
                sia_texture.kind = kind
                sia_material.textures.append(sia_texture)

            sia_mesh.materials.append(sia_material)

        # TODO: Move this inline into the loop above
        for index, normal, uv_coords, tangent in ply_verts:
            vert = mesh_verts[index]
            uv_sets = []
            for uv_set in uv_coords:
                uv_sets.append(data_types.Vector2(*uv_set))
            vertex = data_types.Vertex(
                data_types.Vector3(*vert.co[:]),
                data_types.Vector3(*normal),
                uv_sets,
                data_types.Vector3(*tangent),
            )
            model.bounding_box.update_with_vector(vertex.position)
            sia_mesh.vertices.append(vertex)

        # TODO: Move this inline into the loop above
        for pf in ply_faces:
            sia_mesh.triangles.append(data_types.Triangle(*pf))

        # TODO: These don't need to be fields, it can compute this when writing it.
        sia_mesh.vertices_num = len(sia_mesh.vertices)
        sia_mesh.triangles_num = len(sia_mesh.triangles)

        model.meshes.append(sia_mesh)

        mesh_owner.to_mesh_clear()

    if len(model.meshes) == 0:
        raise Exception("No valid meshes to export")

    with open(filepath, "wb") as file:
        file.write(b"SHSM")

        file.write(pack("<I", 35))

        write_utils.string(file, model.name)

        write_utils.zeros(file, 12)

        write_utils.f32(
            file,
            max(
                model.bounding_box.max_x,
                max(model.bounding_box.max_y, model.bounding_box.max_z),
            ),
        )

        model.bounding_box.write(file)

        write_utils.u32(file, len(model.meshes))

        # Seems like some sort of offset, but where does the magic numbers come from?
        # and do they change per mesh, need to check that out.
        # is it like vertices bytes written?
        vertex_offset = 0
        triangle_offset = 0
        for mesh in model.meshes:
            write_utils.u32(file, vertex_offset)
            write_utils.u32(file, mesh.vertices_num)
            vertex_offset += mesh.vertices_num * 96

            write_utils.u32(file, triangle_offset)
            write_utils.u32(file, mesh.triangles_num * 3)
            triangle_offset += (mesh.triangles_num * 3) * 2

            write_utils.u32(file, mesh.id)
            # Setting byte 4 and 8 to 0, made it crash, no noticable difference when changing the others
            write_utils.full_bytes(file, 8)

        write_utils.u32(file, len(model.meshes))

        for mesh in model.meshes:
            # What is this?
            # almost seems to be a hash or something,
            # it looks like when the material name is the same, so is this byte sequence.
            # write_utils.u32(file, mesh.id)
            # might be the material type, since they need to be specific values for lighting to work.

            if uses_lightmap:
                for byte in [20, 153, 150, 225]:
                    write_utils.u8(
                        file, byte
                    )  # I did mess around with it a little bit as a bitfield, it didn't give any results
            else:
                for byte in [59, 194, 144, 210]:
                    write_utils.u8(file, byte)

            write_utils.zeros(file, 4)
            write_utils.full_bytes(file, 4)
            write_utils.zeros(file, 4)

            write_utils.string(file, mesh.materials[0].name)
            write_utils.u8(file, len(mesh.materials))
            for material in mesh.materials:
                write_utils.string(file, material.kind)
                write_utils.u8(file, len(material.textures))
                for texture in material.textures:
                    texture.write(file)

            write_utils.zeros(file, 64)

        vertices_total_num = 0
        number_of_triangles = 0
        for mesh in model.meshes:
            vertices_total_num += mesh.vertices_num
            number_of_triangles += mesh.triangles_num

        write_utils.u32(file, vertices_total_num)

        model.settings = data_types.Bitfield()
        model.settings[0] = True  # When set to false the entire mesh is gone
        model.settings[
            1
        ] = True  # When set to false there is no color information, only what looks like roughness
        model.settings[
            2
        ] = True  # When I set this to false it kinda does the same thing as the lightmap underneath but with the color texture
        model.settings[
            3
        ] = True  # Weird when I turned this to false, it still showed the lightmap but the texture was projected from like top down
        model.settings[5] = True  # Don't see any difference
        model.settings[9] = True  # Don't see any difference
        write_utils.u32(file, model.settings.number())

        for mesh in model.meshes:
            for vertex in mesh.vertices:
                if model.settings[0]:
                    write_utils.vector3(file, vertex.position)
                if model.settings[1]:
                    write_utils.vector3(file, vertex.normal)
                if model.settings[2]:
                    write_utils.vector2(file, vertex.texture_coords[0])
                if model.settings[3]:
                    if len(vertex.texture_coords) == 1:
                        write_utils.vector2(file, vertex.texture_coords[0])
                    else:
                        write_utils.vector2(file, vertex.texture_coords[1])
                if model.settings[5]:
                    # Thought this could be tangents, but why is there one more value at the end then.
                    write_utils.vector3(file, vertex.tangent)
                    write_utils.f32(file, 1)
                if model.settings[9]:
                    # When I've seen this it has been all F's
                    # as mentioned in the parse_sia file, might be vertex color.
                    # although setting them all to zero I could not see a difference
                    write_utils.full_bytes(file, 4)

        write_utils.u32(file, number_of_triangles * 3)

        for mesh in model.meshes:
            for triangle in mesh.triangles:
                if vertices_total_num > 65535:
                    triangle.write_u32(file)
                else:
                    triangle.write_u16(file)

        write_utils.u32(file, 0)  # some_number
        write_utils.u32(file, 0)  # some_number2

        write_utils.u8(
            file, 0
        )  # num, change this to non-zero without anything else written after, to eat ram.

        write_utils.u32(file, 0)  # instances

        file.write(b"EHSM")

        return {"FINISHED"}

    return {"CANCELED"}
