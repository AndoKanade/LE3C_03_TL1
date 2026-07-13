import bpy
import bpy_extras
import gpu
import gpu_extras.batch
import copy
import math
import mathutils

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

# --- コライダー描画クラス ---
class DrawCollider:
    handle = None

    def draw_collider():
        # GPUに渡す最終的な全頂点座標のリスト
        vertices = {"pos": []}
        
        # GPUに渡す最終的な全辺（ライン）のインデックスリスト
        indices = []
        
        # オフセットを記録するためのリスト
        offsets = []

        # シーン内の全てのオブジェクトを1個ずつ走査するループ
        for obj in bpy.context.scene.objects:
            
            # このオブジェクトの頂点データが全体の何番目から始まるかを記録（オフセット計算）
            current_total_vertices = len(vertices["pos"])
            offset = current_total_vertices
            offsets.append(offset)
            
            # 立方体1個分（ローカル座標系）の8つの頂点を定義
            v0 = [-1.0, -1.0, -1.0] # 手前・左・下
            v1 = [ 1.0, -1.0, -1.0] # 手前・右・下
            v2 = [-1.0,  1.0, -1.0] # 奥・左・下
            v3 = [ 1.0,  1.0, -1.0] # 奥・右・下
            v4 = [-1.0, -1.0,  1.0] # 手前・左・上
            v5 = [ 1.0, -1.0,  1.0] # 手前・右・上
            v6 = [-1.0,  1.0,  1.0] # 奥・左・上
            v7 = [ 1.0,  1.0,  1.0] # 奥・右・上
            
            local_vertices = [v0, v1, v2, v3, v4, v5, v6, v7]
            
            # このオブジェクトのワールド行列（位置・回転・縮小のすべての情報）を取得
            mat = obj.matrix_world
            
            # ローカル頂点を1つずつワールド座標に変換して全体の頂点リストに追加するループ
            for v in local_vertices:
                # 3つの数値をBlenderのVector型に変換
                local_pos = mathutils.Vector(v)
                
                # 行列とベクトルを掛け算してワールド座標系に変換
                world_pos = mat @ local_pos
                
                # 変換された座標を [x, y, z] のリスト形式にして全体のリストに追加
                vertices["pos"].append([world_pos.x, world_pos.y, world_pos.z])
                
            # 立方体の12本の辺を構成する頂点のインデックス組み合わせ（ローカル基準）
            # 下面の4辺
            edge1 = [0, 1]
            edge2 = [1, 3]
            edge3 = [3, 2]
            edge4 = [2, 0]
            # 上面の4辺
            edge5 = [4, 5]
            edge6 = [5, 7]
            edge7 = [7, 6]
            edge8 = [6, 4]
            # 柱となる垂直な4辺
            edge9 = [0, 4]
            edge10 = [1, 5]
            edge11 = [2, 6]
            edge12 = [3, 7]
            
            local_indices = [
                edge1, edge2, edge3, edge4,
                edge5, edge6, edge7, edge8,
                edge9, edge10, edge11, edge12
            ]
            
            # 全体の頂点リストの中での正しいインデックス（オフセット加算）を計算して追加するループ
            for edge in local_indices:
                start_index = edge[0] + offset
                end_index = edge[1] + offset
                indices.append([start_index, end_index])

        # 描画に使うシェーダ（単色塗りつぶし）を準備
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")

        # シェーダ、描画タイプ（ライン）、頂点とインデックスをまとめてバッチを作成
        batch = gpu_extras.batch.batch_for_shader(shader, "LINES", vertices, indices=indices)

        # 線の色を設定（水色：R=0.5, G=1.0, B=1.0, A=1.0）
        color = [0.5, 1.0, 1.0, 1.0]
        
        # シェーダをアクティブにして色を適用
        shader.bind()
        shader.uniform_float("color", color)

        # 3Dビューポートにバッチを描画
        batch.draw(shader)

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
        indent = ''
        for i in range(level):
            indent += "\t"
        
        self.write_and_print(file, indent + obj.type)
        
        trans, rot, scale = obj.matrix_local.decompose()
        rot = rot.to_euler()

        rot.x = math.degrees(rot.x)
        rot.y = math.degrees(rot.y)
        rot.z = math.degrees(rot.z)

        self.write_and_print(file, indent + "  T %f %f %f" % (trans.x, trans.y, trans.z))
        self.write_and_print(file, indent + "  R %f %f %f" % (rot.x, rot.y, rot.z))
        self.write_and_print(file, indent + "  S %f %f %f" % (scale.x, scale.y, scale.z))
        
        if "file_name" in obj:
            self.write_and_print(file, indent + "  N %s" % obj["file_name"])
            
        self.write_and_print(file, indent + "  END")
        self.write_and_print(file, indent + '')

        for child in obj.children:
            self.parse_scene_recursive(file, child, level + 1)

    def export(self, filepath):
        """ファイルに出力"""
        print("シーン情報出力開始... %r" % filepath)
        with open(filepath, "wt", encoding="utf-8") as file:
            file.write("SCENE\n")
            for obj in bpy.context.scene.objects:
                if obj.parent is None:
                    self.parse_scene_recursive(file, obj, 0)

    def execute(self, context):
        print("シーン情報をExportします")
        self.export(self.filepath)
        print("シーン情報をExportしました")
        self.report({'INFO'}, "シーン情報をExportしました")
        return {'FINISHED'}

# --- オペレータクラス：カスタムプロパティ['file_name']追加 ---
class MYADDON_OT_add_filename(bpy.types.Operator):
    """['file_name']カスタムプロパティを追加します"""
    bl_idname = "myaddon.myaddon_ot_add_filename"
    bl_label = "FileName 追加"
    bl_description = "['file_name']カスタムプロパティを追加します"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.object["file_name"] = ""
        return {"FINISHED"}

# --- パネルクラス：ファイル名 ---
class OBJECT_PT_file_name(bpy.types.Panel):
    """オブジェクトのファイルネームパネル"""
    bl_idname = "OBJECT_PT_file_name"
    bl_label = "FileName"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        self.layout.operator(MYADDON_OT_add_filename.bl_idname, text=MYADDON_OT_add_filename.bl_label)

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
    MYADDON_OT_add_filename,
    TOPBAR_MT_my_menu,
    OBJECT_PT_file_name,
)

# アドオン有効化時の処理
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR_MT_my_menu.submenu)

    DrawCollider.handle = bpy.types.SpaceView3D.draw_handler_add(DrawCollider.draw_collider,(),"WINDOW","POST_VIEW")

    print("レベルエディタが有効化されました。")

# アドオン無効化時の処理
def unregister():
    if hasattr(bpy.types, "TOPBAR_MT_editor_menus"):
        try:
            bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR_MT_my_menu.submenu)

            bpy.types.SpaceView3D.draw_handler_remove(DrawCollider.handle,"WINDOW")

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