import bpy
import bmesh
from . import parse_sia


def load(context, filepath):
    sia_file = parse_sia.Model.load(filepath)

    view_layer = context.view_layer
    collection = view_layer.active_layer_collection.collection

    root = bpy.data.objects.new(sia_file.name, None)
    collection.objects.link(root)
    materials = {}

    for (i, mesh) in sia_file.meshes.items():
        me = bpy.data.meshes.new("{}_mesh_{}".format(sia_file.name.lower(), i))
        for material in mesh.materials:
            if material.name not in materials:
                materials[material.name] = bpy.data.materials.new(
                    material.name)
            me.materials.append(materials[material.name])

        bm = bmesh.new()
        uvs = []
        for v in mesh.vertices:
            bm.verts.new((v.position.x, v.position.y,
                          v.position.z))
            uvs.append((v.uv.x, (v.uv.y * -1) + 1))
        bm.verts.ensure_lookup_table()
        for f in mesh.triangles:
            bm.faces.new(
                (bm.verts[f.index1], bm.verts[f.index2], bm.verts[f.index3]))
        bm.faces.ensure_lookup_table()

        bm.to_mesh(me)
        uv_set = me.uv_layers.new().data

        uvs = [i for poly in me.polygons
               for vidx in poly.vertices
               for i in uvs[vidx]]
        uv_set.foreach_set('uv', uvs)
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))

        me.validate(clean_customdata=False)
        me.update(calc_edges=False, calc_edges_loose=False)

        obj = bpy.data.objects.new(me.name, me)
        obj.parent = root
        collection.objects.link(obj)

    view_layer.objects.active = root

    view_layer.update()
    return {'FINISHED'}
