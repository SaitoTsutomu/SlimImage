import os
from math import ceil, log2

import bpy
from bpy.props import BoolProperty, IntProperty

from .register_class import _get_cls


class CSI_OT_slim_image(bpy.types.Operator):
    """イメージをスリムに"""

    bl_idname = "object.slim_image"
    bl_label = "Slim Image"
    bl_description = "Slimming down image files."

    quality: IntProperty() = IntProperty(default=75)  # type: ignore
    to_small: BoolProperty() = BoolProperty(default=True)  # type: ignore

    def execute(self, context):
        os.makedirs("/tmp/img/", exist_ok=True)
        bpy.context.scene.render.image_settings.quality = self.quality
        bpy.context.scene.render.image_settings.file_format = "JPEG"

        bpy.ops.file.unpack_all(method="REMOVE")
        for img in bpy.data.images:
            if img.name == "Render Result":
                continue
            r = 2 ** max(0, ceil(log2(img.size[0] * img.size[1] / 2 ** 20)) // 2)
            img.filepath_raw = "/tmp/img/" + img.name.split(".")[0] + ".jpg"
            if r > 1 and self.to_small:
                img.scale(img.size[0] // r, img.size[1] // r)
            img.save_render(img.filepath_raw, scene=bpy.context.scene)
        bpy.ops.file.pack_all()
        return {"FINISHED"}


class CSI_PT_bit(bpy.types.Panel):
    bl_label = "SlimImage"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"

    def draw(self, context):
        self.layout.prop(context.scene, "quality", text="Quality")
        self.layout.prop(context.scene, "to_small", text="To Small")
        text = CSI_OT_slim_image.bl_label
        prop = self.layout.operator(CSI_OT_slim_image.bl_idname, text=text)
        prop.quality = context.scene.quality
        prop.to_small = context.scene.to_small


ui_classes = _get_cls(__name__)
