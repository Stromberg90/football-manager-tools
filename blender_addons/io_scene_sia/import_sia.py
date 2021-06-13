import bpy
import os
import bmesh
from bpy_extras import node_shader_utils
from bpy_extras.io_utils import unpack_list
from bpy_extras.image_utils import load_image
from . import parse_sia
from . import utils
from . import data_types


def load(context, filepath, addon_preferences):
    sia_file = parse_sia.load(filepath)
    sia_file.name = sia_file.name.decode("utf-8", "replace")

    view_layer = context.view_layer
    collection = view_layer.active_layer_collection.collection

    root = bpy.data.objects.new(sia_file.name, None)
    collection.objects.link(root)

    for (i, mesh) in sia_file.meshes.items():
        materials = {}
        me = bpy.data.meshes.new("{}_mesh_{}".format(sia_file.name.lower(), i))
        for material in mesh.materials:
            material.name = material.name.decode("utf-8", "replace")
            if material.name not in materials:
                materials[material.name] = bpy.data.materials.new(material.name)
            else:
                continue

            mat = materials[material.name]

            wrapped_mat = node_shader_utils.PrincipledBSDFWrapper(
                mat, is_readonly=False, use_nodes=True
            )

            for texture in material.textures:
                texture_path = utils.absolute_asset_path(
                    addon_preferences.base_extracted_textures_path,
                    texture.path.decode("utf-8", "replace"),
                )

                for ext in [".dds", ".tga", ".png", ".jpg", ".jpeg"]:
                    if os.path.exists(texture_path + ext):
                        texture_path = texture_path + ext
                        break

                if texture.kind == data_types.TextureKind.Albedo:
                    wrapped_mat.base_color_texture.image = load_image(texture_path)
                    wrapped_mat.base_color_texture.texcoords = "UV"

            me.materials.append(materials[material.name])

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
