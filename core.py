import os
from dataclasses import dataclass

import bpy
from bpy.props import BoolProperty, IntProperty

from .register_class import _get_cls


@dataclass
class ChangeImageSettings:
    image: bpy.types.Image
    quality: int

    def __enter__(self):
        n = self.image.depth // (self.image.is_float * 3 + 1) // 8
        self.file_format = "JPEG" if n % 2 else "PNG"
        self.color_mode = ["BW", "RGBA", "RGB", "RGBA"][n - 1]
        self.__exit__(None, None, None)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        stng = bpy.context.scene.render.image_settings
        self.quality, stng.quality = stng.quality, self.quality
        # file_formatを変えるとcolor_modeが変わる可能性があるので、この順でないといけない
        self.file_format, self.color_mode, stng.file_format, stng.color_mode = (
            stng.file_format,
            stng.color_mode,
            self.file_format,
            self.color_mode,
        )


class CSI_OT_slim_image(bpy.types.Operator):
    """イメージをスリムに"""

    bl_idname = "object.slim_image"
    bl_label = "Slim Image"
    bl_description = "Slimming down image files."

    quality: IntProperty() = IntProperty(default=75)  # type: ignore
    to_small: BoolProperty() = BoolProperty(default=True)  # type: ignore

    def execute(self, context):
        bpy.context.scene.view_settings.view_transform = "Standard"
        os.makedirs("/tmp/img/", exist_ok=True)
        bpy.ops.file.unpack_all(method="REMOVE")
        for img in bpy.data.images:
            if img.name == "Render Result":
                continue
            if self.to_small:
                while img.size[0] > 1024 and img.size[1] > 1024:
                    img.scale(img.size[0] // 2, img.size[1] // 2)
            img.filepath_raw = "/tmp/img/" + img.name.split(".")[0] + ".jpg"
            with ChangeImageSettings(img, self.quality):
                img.save_render(img.filepath_raw, scene=bpy.context.scene)
            img.reload()
        bpy.ops.file.pack_all()
        # bpy.ops.image.save_all_modified()
        bpy.context.scene.view_settings.view_transform = "Filmic"
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
