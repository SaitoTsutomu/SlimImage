import bpy
import numpy as np

bl_info = {
    "name": "ShapeKeyPaste",
    "author": "tsutomu",
    "version": (0, 1),
    "blender": (3, 1, 0),
    "support": "TESTING",
    "category": "Object",
    "description": "",
    "location": "View3D > Object",
    "warning": "",
    "doc_url": "https://github.com/SaitoTsutomu/ShapeKeyPaste",
}


def set_wireframe():
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.type = "WIREFRAME"


class CSK_OT_select_diff_objs(bpy.types.Operator):
    """2つのオブジェクトの異なる点を選択"""

    bl_idname = "object.select_diff_objs"
    bl_label = "Sel Diff 2 Obj"
    bl_description = "Select the different vertices of 2 objects."

    def execute(self, context):
        objs = [obj for obj in bpy.context.objects if obj.type == "MESH"]
        if len(objs) != 2:
            self.report({"INFO"}, "Select 2 objects.")
            return {"CANCELLED"}
        bpy.ops.object.mode_set(mode="EDIT")  # for deselect
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")  # for select
        dif = set(tuple(vtx.co) for vtx in objs[0].data.vertices) ^ set(
            tuple(vtx.co) for vtx in objs[1].data.vertices
        )
        for obj in objs:
            for i, vtx in enumerate(obj.data.vertices):
                if tuple(vtx.co) in dif:
                    obj.data.vertices[i].select = True
        bpy.ops.object.mode_set(mode="EDIT")  # for confirm
        set_wireframe()
        return {"FINISHED"}


class CSK_OT_select_diff_from_basis(bpy.types.Operator):
    """シェイプキーのBasisの位置が異なる点を選択"""

    bl_idname = "object.select_diff_from_basis"
    bl_label = "Select Diff from basis"
    bl_description = "Select the different vertices from basis and active shape key."

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
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")  # for select
        kb = obj.data.shape_keys.key_blocks
        for i in range(len(obj.data.vertices)):
            c1 = kb[0].data[i].co
            c2 = kb[target_key_id].data[i].co
            if not np.isclose(c1, c2, atol=1e-5).all():
                obj.data.vertices[i].select = True
        bpy.ops.object.mode_set(mode="EDIT")  # for confirm
        set_wireframe()
        return {"FINISHED"}


class CSK_OT_copy_vertices(bpy.types.Operator):
    """選択している点のインデックスをコピー"""

    bl_idname = "object.copy_vertices"
    bl_label = "Copy Vert"
    bl_description = "Copy the selected vertices from active shape key."

    def execute(self, context):
        if context.mode != "EDIT_MESH":
            self.report({"WARNING"}, "Enter to edit mode.")
            return {"CANCELLED"}
        obj = context.edit_object
        s = " ".join(str(i) for i, v in enumerate(obj.data.vertices) if v.select)
        context.window_manager.clipboard = f"ShapeKeyPaste {obj.active_shape_key_index} " + s


class CSK_OT_paste_vertices(bpy.types.Operator):
    """コピーされた点の位置をペースト"""

    bl_idname = "object.paste_vertices"
    bl_label = "Paste Vert"
    bl_description = "Paste the position of vertices to active shape key."

    def execute(self, context):
        if context.mode != "EDIT_MESH":
            self.report({"WARNING"}, "Enter to edit mode.")
            return {"CANCELLED"}
        obj = context.edit_object
        ss = context.window_manager.clipboard.split()
        if len(ss) < 3 or ss[0] != "ShapeKeyPaste" or obj.data.shape_keys:
            self.report({"WARNING"}, "No data in the clipboard or no shape keys.")
            return {"CANCELLED"}
        kb = obj.data.shape_keys.key_blocks
        from_key_id = int(ss[1])
        if not (0 <= from_key_id < len(kb)):
            self.report({"WARNING"}, "Illegal key id.")
            return {"CANCELLED"}
        bpy.ops.object.mode_set(mode="OBJECT")

        to_key_id = obj.active_shape_key_index
        for s in ss[2:]:
            idx = int(s)
            kb[to_key_id].data[idx].co = kb[from_key_id].data[idx].co
        bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}


class CSK_PT_bit(bpy.types.Panel):
    bl_label = "ShapeKeyPaste"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"

    def draw(self, context):
        text = CSK_OT_select_diff_objs.bl_label
        self.layout.operator(CSK_OT_select_diff_objs.bl_idname, text=text)
        text = CSK_OT_select_diff_from_basis.bl_label
        self.layout.operator(CSK_OT_select_diff_from_basis.bl_idname, text=text)

        self.layout.separator()
        text = CSK_OT_copy_vertices.bl_label
        self.layout.operator(CSK_OT_copy_vertices.bl_idname, text=text)
        text = CSK_OT_paste_vertices.bl_label
        self.layout.operator(CSK_OT_paste_vertices.bl_idname, text=text)


ui_classes = (
    CSK_OT_select_diff_objs,
    CSK_OT_select_diff_from_basis,
    CSK_OT_copy_vertices,
    CSK_OT_paste_vertices,
    CSK_PT_bit,
)


def register():
    for ui_class in ui_classes:
        bpy.utils.register_class(ui_class)


def unregister():
    for ui_class in ui_classes:
        bpy.utils.unregister_class(ui_class)


if __name__ == "__main__":
    register()
