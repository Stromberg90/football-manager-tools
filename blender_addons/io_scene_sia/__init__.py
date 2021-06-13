if "bpy" in locals():
    import importlib
    if "export_sia" in locals():
        importlib.reload(export_sia)
    if "import_sia" in locals():
        importlib.reload(import_sia)

import bpy

from bpy.props import (
    StringProperty,
)

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
    "version": (0, 1, 0),
    "blender": (2, 91, 2),
    "location": "File > Import-Export",
    "description": "Import-Export SIA",
    "category": "Import-Export",
    "tracker_url": "https://github.com/Stromberg90/football-manager-tools/issues",
}

@orientation_helper(axis_forward='Y', axis_up='Z')
class ExportSIA(bpy.types.Operator, ExportHelper):
    """Save a SIA File"""

    bl_idname = "export_scene.sia"
    bl_label = 'Export SIA'
    bl_options = {'PRESET'}

    filename_ext = ".sia"
    filter_glob: StringProperty(
        default="*.sia",
        options={'HIDDEN'},
    )

    def execute(self, context):
        from . import export_sia

        return export_sia.save(context, self.filepath, self.axis_forward, self.axis_up, context.preferences.addons[__name__].preferences)


class ImportSIA(bpy.types.Operator, ExportHelper):
    """Save a SIA File"""

    bl_idname = "import_scene.sia"
    bl_label = 'Import SIA'
    bl_options = {'PRESET'}

    filename_ext = ".sia"
    filter_glob: StringProperty(
        default="*.sia",
        options={'HIDDEN'},
    )

    def execute(self, context):
        from . import import_sia

        return import_sia.load(context, self.filepath, context.preferences.addons[__name__].preferences)

class IoSiaPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    base_extracted_textures_path: StringProperty(
        name="Base Extracted Textures Path",
        description="Path to extracted from football manager base folder",
        default="",
        subtype="DIR_PATH"
    )

    base_textures_path: StringProperty(
        name="Base Custom Textures Path",
        description="Path to custom textures base folder",
        default="",
        subtype="DIR_PATH"
    )

    base_extracted_meshes_path: StringProperty(
        name="Base Extracted Meshes Path",
        description="Path to meshes from football manager base folder",
        default="",
        subtype="DIR_PATH"
    )

    base_meshes_path: StringProperty(
        name="Base Custom Meshes Path",
        description="Path to custom meshes base folder",
        default="",
        subtype="DIR_PATH"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "base_extracted_textures_path")
        layout.prop(self, "base_textures_path")
        layout.prop(self, "base_extracted_meshes_path")
        layout.prop(self, "base_meshes_path")

classes = (
    ExportSIA,
    ImportSIA,
    IoSiaPreferences
)


def menu_func_export(self, context):
    self.layout.operator(ExportSIA.bl_idname,
                         text="Football Manager 2021 Mesh (.sia)")


def menu_func_import(self, context):
    self.layout.operator(ImportSIA.bl_idname,
                         text="Football Manager 2021 Mesh (.sia)")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
