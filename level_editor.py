import bpy
import bpy_extras
import math

# ブレンダーに登録するアドオン情報
bl_info = {
    "name": "レベルエディタ",
    "author": "Taro Kamata",
    "version": (1, 0),
    "blender": (3, 3, 1),
    "location": "",
    "description": "レベルエディタ",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"
}

# マニュアルメニューの項目描画
def draw_menu_manual(self, context):
    self.layout.operator("wm.url_open_preset", text="Manual", icon='HELP')

# --- オペレータクラス：頂点を伸ばす ---
class MYADDON_OT_stretch_vertex(bpy.types.Operator):
    bl_idname = "myaddon.myddon_ot_stretch_vertex"
    bl_label = "頂点を伸ばす"
    bl_description = "頂点座標を引っ張って伸ばします"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.data.objects["Cube"].data.vertices[0].co.x += 1.0
        print("頂点を伸ばしました")
        return {'FINISHED'}

# --- オペレータクラス：ICO球生成 ---
class MYADDON_OT_create_ico_sphere(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_create_object"
    bl_label = "ICO球生成"
    bl_description = "ICO球を生成します"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_ico_sphere_add()
        print("ICO球を生成しました。")
        return {'FINISHED'}

# --- オペレータクラス：シーン出力 ---
class MYADDON_OT_export_scene(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "myaddon.myaddon_ot_export_scene"
    bl_label = "シーン出力"
    bl_description = "シーン情報をExportします"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".scene"

    def write_and_print(self, file, text):
        file.write(text + "\n")
        print(text)

    def parse_scene_recursive(self, file, obj, level):
        """シーン解析用再帰関数"""
        
        # 深さ分インデントする（タブを挿入）
        indent = ''
        for i in range(level):
            indent += "\t"
        
        # オブジェクト名書き込み
        self.write_and_print(file, indent + obj.type + " - " + obj.name)
        
        # 行列分解と回転角変換
        trans, rot, scale = obj.matrix_local.decompose()
        rot = rot.to_euler()

        rot.x = math.degrees(rot.x)
        rot.y = math.degrees(rot.y)
        rot.z = math.degrees(rot.z)

        # トランスフォーム情報を表示
        self.write_and_print(file, indent + "  Trans(%f,%f,%f)" % (trans.x, trans.y, trans.z))
        self.write_and_print(file, indent + "  Rot(%f,%f,%f)" % (rot.x, rot.y, rot.z))
        self.write_and_print(file, indent + "  Scale(%f,%f,%f)" % (scale.x, scale.y, scale.z))
        self.write_and_print(file, indent + '')

        # 子ノードへ進む（深さが1上がる）
        for child in obj.children:
            self.parse_scene_recursive(file, child, level + 1)

    def export(self, filepath):
        """ファイルに出力"""
        print("シーン情報出力開始... %r" % filepath)
        
        with open(filepath, "wt", encoding="utf-8") as file:
            file.write("SCENE\n") # 🌟【修正】資料の1行目に合わせて改行を調整
            
            # 🌟【修正】二重出力を防ぐため、親を持たない（ルート）オブジェクトのみを最初に呼び出す
            for obj in bpy.context.scene.objects:
                if obj.parent is None:
                    self.parse_scene_recursive(file, obj, 0)

    def execute(self, context):
        print("シーン情報をExportします")
        self.export(self.filepath)
        print("シーン情報をExportしました")
        self.report({'INFO'}, "シーン情報をExportしました")
        return {'FINISHED'}

# --- メメニュークラス ---
class TOPBAR_MT_my_menu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_my_menu"
    bl_label = "MyMenu"
    bl_description = "拡張メニュー by " + bl_info["author"]

    def draw(self, context):
        self.layout.operator(MYADDON_OT_stretch_vertex.bl_idname, text=MYADDON_OT_stretch_vertex.bl_label)
        self.layout.operator(MYADDON_OT_create_ico_sphere.bl_idname, text=MYADDON_OT_create_ico_sphere.bl_label) 
        self.layout.operator(MYADDON_OT_export_scene.bl_idname, text=MYADDON_OT_export_scene.bl_label)

    def submenu(self, context):
        self.layout.menu(TOPBAR_MT_my_menu.bl_idname)

# 登録対象のクラス一覧
classes = (
    MYADDON_OT_stretch_vertex,
    MYADDON_OT_create_ico_sphere,
    MYADDON_OT_export_scene,
    TOPBAR_MT_my_menu,
)

# アドオン有効化時の処理
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR_MT_my_menu.submenu)
    print("レベルエディタが有効化されました。")

# アドオン無効化時の処理
def unregister():
    if hasattr(bpy.types, "TOPBAR_MT_editor_menus"):
        try:
            bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR_MT_my_menu.submenu)
        except Exception as e:
            print(f"メニュー削除エラー: {e}")
            
    for cls in classes:
        if hasattr(bpy.utils, "is_class_registered") and bpy.utils.is_class_registered(cls):
            try:
                bpy.utils.unregister_class(cls)
            except Exception as e:
                print(f"クラス解除エラー ({cls.__name__}): {e}")
                
    print("レベルエディタが無効化されました。")

if __name__ == "__main__":
    register()