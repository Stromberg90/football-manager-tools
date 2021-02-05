import bpy
import bmesh
import ntpath
import os
import sys
from collections import OrderedDict
from . import parse_sia


def load(context, filepath):
    sia_file = parse_sia.Model.load(filepath)

    view_layer = context.view_layer
    collection = view_layer.active_layer_collection.collection

    root = bpy.data.objects.new(sia_file.name, None)
    collection.objects.link(root)
    for (i, mesh) in sia_file.meshes.items():
        for material in mesh.materials:
            print("Name: ", material.name)
            print("Kind: ", material.kind)
            for texture in material.textures:
                print(" Name: ", texture.name)
                print(" ID: ", texture.id)

        me = bpy.data.meshes.new("{}_mesh_{}".format(sia_file.name.lower(), i))
        bm = bmesh.new()
        uvs = []
        for v in mesh.vertices:
            bm.verts.new((v.position.x, v.position.y,
                          v.position.z))
            uvs.append((v.uv.x, v.uv.y))
        bm.verts.ensure_lookup_table()
        for f in mesh.triangles:
            bm.faces.new(
                (bm.verts[f.index1], bm.verts[f.index2], bm.verts[f.index3]))
        bm.faces.ensure_lookup_table()

        bm.to_mesh(me)
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        me.uv_layers.new(do_init=False)
        for i in range(len(uvs)):
            uv_loop = me.uv_layers[0].data[i]
            uv_loop.uv = uvs[i]

        me.validate(clean_customdata=False)
        me.update(calc_edges=False, calc_edges_loose=False)

        obj = bpy.data.objects.new(me.name, me)
        obj.parent = root
        collection.objects.link(obj)

    view_layer.objects.active = root

    view_layer.update()
    return {'FINISHED'}
