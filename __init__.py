import bpy
import numpy as np

bl_info = {
    "name": "ShapeKeyBit",
    "author": "tsutomu",
    "version": (0, 1),
    "blender": (3, 1, 0),
    "support": "TESTING",
    "category": "Object",
    "description": "",
    "location": "View3D > Object",
    "warning": "",
    "doc_url": "https://github.com/SaitoTsutomu/ShapeKeyBit",
}


class CSK_OT_select_diff_from_basis(bpy.types.Operator):
    """シェイプキーのBasisの位置が異なる点を選択"""

    bl_idname = "object.select_diff_from_basis"
    bl_label = "Select Diff"
    bl_description = "Select different vertices from basis shape key and active shape key."

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != "MESH" or not obj.data.shape_keys:
            self.report({"WARNING"}, "Select an object with shape key.")
            return {"CANCELLED"}
        target_key_id = obj.active_shape_key_index
        if not target_key_id:
            self.report({"WARNING"}, "Select a shape key WITHOUT Basis.")
            return {"CANCELLED"}
        bpy.ops.object.mode_set(mode="EDIT")  # for deselect
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")  # for select
        kb = obj.data.shape_keys.key_blocks
        for i in range(len(obj.data.vertices)):
            c1 = kb[0].data[i].co
            c2 = kb[target_key_id].data[i].co
            if not np.isclose(c1, c2, atol=1e-5).all():
                obj.data.vertices[i].select = True
        bpy.ops.object.mode_set(mode="EDIT")  # for confirm
        bpy.ops.mesh.select_mode(type="VERT")
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "WIREFRAME"
        return {"FINISHED"}


class CSK_OT_set_vert_from_active(bpy.types.Operator):
    """選択している点のシェイプキーの位置をターゲットに反映"""

    bl_idname = "object.set_vert_from_active"
    bl_label = "Set Vert"
    bl_description = "Set vertices from active shape key to target shape key."

    to_shape_key: bpy.props.IntProperty()  # type: ignore

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Select an object with shape key.")
            return {"CANCELLED"}
        from_key_id = obj.active_shape_key_index
        bpy.ops.object.mode_set(mode="OBJECT")
        kb = obj.data.shape_keys.key_blocks
        for i in range(len(obj.data.vertices)):
            if obj.data.vertices[i].select:
                kb[self.to_shape_key].data[i].co = kb[from_key_id].data[i].co
        return {"FINISHED"}


class CSK_OT_save_vert_to_csv(bpy.types.Operator):
    """アクティブシェイプキーの選択した点の位置をCSVに出力"""

    bl_idname = "object.save_vert_to_csv"
    bl_label = "Save CSV"
    bl_description = "Save the selected vertices of active shape key to the CSV file."

    filepath: bpy.props.StringProperty()  # type: ignore # noqa

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Select an object with shape key.")
            return {"CANCELLED"}
        key_id = obj.active_shape_key_index
        bpy.ops.object.mode_set(mode="OBJECT")
        with open(self.filepath, "w") as fp:
            for i, skp in enumerate(obj.data.shape_keys.key_blocks[key_id].data):
                if obj.data.vertices[i].select:
                    fp.write(f"{key_id},{i},{skp.co.x:.8f},{skp.co.y:.8f},{skp.co.z:.8f}\n")
        return {"FINISHED"}


class CSK_OT_load_vert_from_csv(bpy.types.Operator):
    """CSVからシェイプキーの点の位置を読込"""

    bl_idname = "object.load_vert_from_csv"
    bl_label = "Load CSV"
    bl_description = "Load vertices from the CSV file."

    filepath: bpy.props.StringProperty()  # type: ignore # noqa

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Select an object with shape key.")
            return {"CANCELLED"}
        bpy.ops.object.mode_set(mode="OBJECT")
        with open(self.filepath) as fp:
            for s in fp:
                key_id, idx, x, y, z = s.split(",")
                key_id, idx = map(int, (key_id, idx))
                x, y, z = map(float, (x, y, z))
                obj.data.shape_keys.key_blocks[key_id].data[idx].co = x, y, z
        return {"FINISHED"}


class CSK_PT_bit(bpy.types.Panel):
    bl_label = "ShapeKeyBit"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"

    def draw(self, context):
        text = CSK_OT_select_diff_from_basis.bl_label
        self.layout.operator(CSK_OT_select_diff_from_basis.bl_idname, text=text)
        self.layout.separator()
        self.layout.prop(context.scene, "to_shape_key", text="Target ShapeKey Index")
        prop = self.layout.operator(
            CSK_OT_set_vert_from_active.bl_idname, text=CSK_OT_set_vert_from_active.bl_label
        )
        prop.to_shape_key = context.scene.to_shape_key
        self.layout.separator()
        text = CSK_OT_save_vert_to_csv.bl_label
        self.layout.operator(CSK_OT_save_vert_to_csv.bl_idname, text=text)
        self.layout.separator()
        text = CSK_OT_load_vert_from_csv.bl_label
        self.layout.operator(CSK_OT_load_vert_from_csv.bl_idname, text=text)


ui_classes = (
    CSK_OT_select_diff_from_basis,
    CSK_OT_set_vert_from_active,
    CSK_OT_save_vert_to_csv,
    CSK_OT_load_vert_from_csv,
    CSK_PT_bit,
)


def register():
    for ui_class in ui_classes:
        bpy.utils.register_class(ui_class)
    bpy.types.Scene.to_shape_key = bpy.props.IntProperty(default=1)


def unregister():
    for ui_class in ui_classes:
        bpy.utils.unregister_class(ui_class)
    del bpy.types.Scene.to_shape_key


if __name__ == "__main__":
    register()
