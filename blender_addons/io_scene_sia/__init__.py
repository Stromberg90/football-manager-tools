if "bpy" in locals():
    import importlib

    if "export_sia" in locals():
        importlib.reload(export_sia)
    if "import_sia" in locals():
        importlib.reload(import_sia)

import bpy

from bpy.props import StringProperty, BoolProperty, EnumProperty

from bpy_extras.io_utils import (
    ExportHelper,
    ImportHelper,
    orientation_helper,
    path_reference_mode,
    axis_conversion,
)

bl_info = {
    "name": "SIA Format",
    "author": "Andreas Strømberg",
    "version": (1, 4, 0),
    "blender": (4, 0, 0),
    "location": "File > Import-Export",
    "description": "Import-Export SIA",
    "category": "Import-Export",
    "tracker_url": "https://github.com/Stromberg90/football-manager-tools/issues",
}


@orientation_helper(axis_forward="Y", axis_up="Z")
class ExportSIA(bpy.types.Operator, ExportHelper):
    """Saves a SIA File"""

    bl_idname = "export_scene.sia"
    bl_label = "Export SIA"
    bl_options = {"PRESET"}

    filename_ext = ".sia"
    filter_glob: StringProperty(
        default="*.sia",
        options={"HIDDEN"},
    )

    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
    )

    def execute(self, context):
        from . import export_sia

        return export_sia.save(
            context,
            self.filepath,
            context.preferences.addons[__name__].preferences,
            self.axis_forward,
            self.axis_up,
            self.use_selection,
        )


class ImportSIA(bpy.types.Operator, ExportHelper):
    """Imports a SIA File"""

    bl_idname = "import_scene.sia"
    bl_label = "Import SIA"
    bl_options = {"PRESET"}

    filename_ext = ".sia"
    filter_glob: StringProperty(
        default="*.sia",
        options={"HIDDEN"},
    )

    def execute(self, context):
        from . import import_sia

        return import_sia.load(
            context,
            self.filepath,
            context.preferences.addons[__name__].preferences,
        )


class IoSiaPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    base_extracted_textures_path: StringProperty(
        name="Extracted Textures",
        description="Path to extracted from football manager base folder",
        default="",
        subtype="DIR_PATH",
    )

    base_textures_path: StringProperty(
        name="Custom Textures",
        description="Path to custom textures base folder",
        default="",
        subtype="DIR_PATH",
    )

    base_extracted_meshes_path: StringProperty(
        name="Extracted Meshes",
        description="Path to meshes from football manager base folder",
        default="",
        subtype="DIR_PATH",
    )

    base_meshes_path: StringProperty(
        name="Custom Meshes",
        description="Path to custom meshes base folder",
        default="",
        subtype="DIR_PATH",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "base_extracted_textures_path")
        layout.prop(self, "base_textures_path")
        layout.prop(self, "base_extracted_meshes_path")
        layout.prop(self, "base_meshes_path")


class SIA_PT_export_include(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_MESH_OT_sia"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "use_selection")


class SIA_PT_MaterialPanel(bpy.types.Panel):
    bl_label = "FM Properties"
    bl_idname = "SIA_PT_MaterialPanel_layout"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        material = context.material
        if material is None:
            return False
        if material.node_tree is None:
            return False
        nodes = material.node_tree.nodes
        for node in nodes:
            if node.bl_idname == "ShaderNodeBsdfPrincipled":
                nodes.remove(node)
            elif node.bl_idname == "ShaderNodeOutputMaterial":
                output_node = node
        surface_node = output_node.inputs["Surface"]
        if len(surface_node.links) == 0:
            return False
        if "FM Material" in surface_node.links[0].from_node.node_tree.name:
            return True
        return False

    def draw(self, context):
        layout = self.layout

        material = context.material

        layout.prop(material, "FM_SHADER", text="Shader")


class SIA_PT_ObjectPanel(bpy.types.Panel):
    bl_label = "FM Instance"
    bl_idname = "SIA_PT_ObjectPanel_layout"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        object = context.object
        if object.get("FM_INSTANCE_KIND") is not None:
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout

        object = context.object

        layout.prop(object, "FM_INSTANCE_KIND", text="Kind")
        layout.prop(object, "FM_INSTANCE_NAME", text="Name")
        layout.prop(object, "FM_INSTANCE_PATH", text="Path")

classes = (
    ExportSIA,
    SIA_PT_export_include,
    ImportSIA,
    IoSiaPreferences,
    SIA_PT_MaterialPanel,
    SIA_PT_ObjectPanel,
)


def menu_func_export(self, context):
    self.layout.operator(ExportSIA.bl_idname, text="Football Manager 2024 Mesh (.sia)")


def menu_func_import(self, context):
    self.layout.operator(ImportSIA.bl_idname, text="Football Manager 2024 Mesh (.sia)")


def material_kind_to_enum(kind: str) -> str:
    if kind == "static":
        return "STATIC"
    elif kind == "static_lightmapped":
        return "STATIC_LIGHTMAPPED"
    elif kind == "skin":
        return "SKIN"
    elif kind == "match_ball":
        return "MATCH_BALL"
    elif kind == "alpha_tested_hair":
        return "ALPHA_TESTED_HAIR"
    elif kind == "netting":
        return "NETTING"
    elif kind == "ball":
        return "BALL"
    elif kind == "hair":
        return "HAIR"
    elif kind == "light":
        return "LIGHT"
    elif kind == "skinned":
        return "SKINNED"
    else:
        return "STATIC"


def register():
    bpy.types.Object.FM_INSTANCE_KIND = bpy.props.IntProperty()
    bpy.types.Object.FM_INSTANCE_NAME = bpy.props.StringProperty()
    bpy.types.Object.FM_INSTANCE_PATH = bpy.props.StringProperty()
    bpy.types.Material.FM_SHADER = bpy.props.EnumProperty(
        items=[
            ("STATIC", "static", ""),
            ("STATIC_LIGHTMAPPED", "static_lightmapped", ""),
            ("SKIN", "skin", ""),
            ("MATCH_BALL", "match_ball", ""),
            ("ALPHA_TESTED_HAIR", "alpha_tested_hair", ""),
            ("NETTING", "netting", ""),
            ("BALL", "ball", ""),
            ("HAIR", "hair", ""),
            ("LIGHT", "light", ""),
            ("SKINNED", "skinned", ""),
        ]
    )

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    del bpy.types.Object.FM_INSTANCE_KIND
    del bpy.types.Object.FM_INSTANCE_NAME
    del bpy.types.Object.FM_INSTANCE_PATH
    del bpy.types.Material.FM_SHADER

    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
