import bpy
import os
import bmesh
from bpy_extras import node_shader_utils
from bpy_extras.image_utils import load_image
from . import parse_sia
from . import utils
from . import data_types


def load(context, filepath, addon_preferences):
    node_group_name = "FM Material v1.0"
    fm_material_path = os.path.realpath(__file__)
    fm_material_path = os.path.dirname(fm_material_path)
    fm_material_path = bpy.path.abspath(
        fm_material_path + "/fm_material.blend/NodeTree"
    )
    fm_material = None
    append_node_group = True
    for node_group in bpy.data.node_groups:
        if node_group.name == node_group_name:
            append_node_group = False
            fm_material = node_group
            break
    if append_node_group:
        bpy.ops.wm.append(
            directory=fm_material_path, filename=node_group_name, link=False
        )
        for node_group in bpy.data.node_groups:
            if node_group.name == node_group_name:
                fm_material = node_group
                break

    sia_file = parse_sia.load(filepath)
    sia_file.name = sia_file.name.decode("utf-8", "replace")

    view_layer = context.view_layer
    collection = view_layer.active_layer_collection.collection

    root = bpy.data.objects.new(sia_file.name, None)
    collection.objects.link(root)

    materials = {}

    for mesh in sia_file.meshes:
        me = bpy.data.meshes.new("{}_mesh_{}".format(sia_file.name.lower(), mesh.id))
        for material in mesh.materials:
            material.name = material.name.decode("utf-8", "replace")
            if material not in materials:
                materials[material] = bpy.data.materials.new(material.name)

            mat = materials[material]

            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            for node in nodes:
                if node.bl_idname == "ShaderNodeBsdfPrincipled":
                    nodes.remove(node)
                elif node.bl_idname == "ShaderNodeOutputMaterial":
                    output_node = node

            node_group = nodes.new("ShaderNodeGroup")
            node_group.node_tree = fm_material

            mat.node_tree.links.new(
                output_node.inputs["Surface"], node_group.outputs["BSDF"]
            )
            for texture in material.textures:
                texture_path = utils.absolute_asset_path(
                    addon_preferences.base_extracted_textures_path,
                    texture.path.decode("utf-8", "replace"),
                )
                alternative_texture_path = utils.absolute_asset_path(
                    addon_preferences.base_textures_path,
                    texture.path.decode("utf-8", "replace"),
                )
                texture_base = os.path.splitext(texture_path)[0]
                alternative_texture_base = os.path.splitext(alternative_texture_path)[0]

                ext = ".dds"
                if os.path.exists(texture_base + ext):
                    texture_path = texture_base + ext
                elif os.path.exists(alternative_texture_base + ext):
                    texture_path = alternative_texture_base + ext

                if not os.path.exists(texture_path):
                    continue

                if texture.kind == data_types.TextureKind.Albedo:
                    albedo = nodes.new("ShaderNodeTexImage")
                    mat.node_tree.links.new(
                        node_group.inputs["Albedo"], albedo.outputs["Color"]
                    )
                    texture = bpy.data.images.load(texture_path, check_existing=True)
                    albedo.image = texture
                elif (
                    texture.kind
                    == data_types.TextureKind.RoughnessMetallicAmbientOcclusion
                ):
                    ro_me_ao = nodes.new("ShaderNodeTexImage")
                    mat.node_tree.links.new(
                        node_group.inputs["Roughness Metallic AO"],
                        ro_me_ao.outputs["Color"],
                    )
                    texture = bpy.data.images.load(texture_path, check_existing=True)
                    texture.colorspace_settings.name = "Linear"
                    ro_me_ao.image = texture
                elif texture.kind == data_types.TextureKind.Normal:
                    normal = nodes.new("ShaderNodeTexImage")
                    mat.node_tree.links.new(
                        node_group.inputs["Normal"],
                        normal.outputs["Color"],
                    )
                    mat.node_tree.links.new(
                        node_group.inputs["Normal Alpha"],
                        normal.outputs["Alpha"],
                    )
                    texture = bpy.data.images.load(texture_path, check_existing=True)
                    texture.colorspace_settings.name = "Non-Color"
                    normal.image = texture
                elif texture.kind == data_types.TextureKind.Mask:
                    mask = nodes.new("ShaderNodeTexImage")
                    mat.node_tree.links.new(
                        node_group.inputs["Mask"],
                        mask.outputs["Color"],
                    )
                    texture = bpy.data.images.load(texture_path, check_existing=True)
                    texture.colorspace_settings.name = "Linear"
                    mask.image = texture

            me.materials.append(materials[material])

        bm = bmesh.new()
        uvs = []
        for v in mesh.vertices:
            bm.verts.new((v.position.x, v.position.y, v.position.z))
            uvs.append((v.uv.x, (v.uv.y * -1) + 1))
        bm.verts.ensure_lookup_table()
        for f in mesh.triangles:
            bm.faces.new((bm.verts[f.index1], bm.verts[f.index2], bm.verts[f.index3]))
        bm.faces.ensure_lookup_table()

        bm.to_mesh(me)
        uv_set = me.uv_layers.new().data

        uvs = [i for poly in me.polygons for vidx in poly.vertices for i in uvs[vidx]]
        uv_set.foreach_set("uv", uvs)
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))

        me.validate(clean_customdata=False)
        me.update(calc_edges=False, calc_edges_loose=False)

        obj = bpy.data.objects.new(me.name, me)
        obj.parent = root
        collection.objects.link(obj)

    view_layer.objects.active = root

    view_layer.update()
    return {"FINISHED"}
