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

# --- オペレータクラス：コライダーカスタムプロパティ追加 ---
class MYADDON_OT_add_collider(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_collider"
    bl_label = "コライダー 追加"
    bl_description = "['collider']カスタムプロパティを追加します"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.object["collider"] = "BOX"
        context.object["collider_center"] = mathutils.Vector((0, 0, 0))
        context.object["collider_size"] = mathutils.Vector((2, 2, 2))
        return {"FINISHED"}

# --- コライダー描画クラス ---
# --- コライダー描画クラス ---
class DrawCollider:
    handle = None

    def draw_collider():
        # GPUに渡す最終的な全頂点座標のリスト
        vertices = {"pos": []}
        
        # GPUに渡す最終的な全辺（ライン）のインデックスリスト
        indices = []

        # 立方体の中心（オブジェクトの位置）から、各頂点がどの方向にどれくらいずれているか（ローカル座標）
        offsets = [
            [-0.5, -0.5, -0.5], # 0番目: 左下前
            [ 0.5, -0.5, -0.5], # 1番目: 右下前
            [-0.5,  0.5, -0.5], # 2番目: 左上前
            [ 0.5,  0.5, -0.5], # 3番目: 右上前
            [-0.5, -0.5,  0.5], # 4番目: 左下奥
            [ 0.5, -0.5,  0.5], # 5番目: 右下奥
            [-0.5,  0.5,  0.5], # 6番目: 左上奥
            [ 0.5,  0.5,  0.5], # 7番目: 右上奥
        ]

        # シーン内の全てのオブジェクトを1個ずつ走査するループ
        for obj in bpy.context.scene.objects:

            # コライダープロパティがなければ、描画をスキップ
            if not "collider" in obj:
                continue

            # --- スライド1枚目「プロパティ取得」の処理 ---
            # 中心点、サイズの変数を宣言（初期値を入れておく）
            center = mathutils.Vector((0, 0, 0))
            size = mathutils.Vector((2, 2, 2))

            # カスタムプロパティから値を取得して変数に格納
            center[0] = obj["collider_center"][0]
            center[1] = obj["collider_center"][1]
            center[2] = obj["collider_center"][2]
            
            size[0] = obj["collider_size"][0]
            size[1] = obj["collider_size"][1]
            size[2] = obj["collider_size"][2]

            # 追加前の頂点数を開始インデックスとして記録
            start = len(vertices["pos"])

            # --- スライド2枚目「座標に反映」のループ処理 ---
            # Boxの8頂点分回す
            for offset in offsets:
                
                # ① object.location の代わりにコライダーの中心点を使う
                # カスタムプロパティから取得したローカルの中心座標をコピー
                pos = copy.copy(center)
                
                # 中心点を基準に各頂点ごとにずらす（ローカル座標系での計算）
                pos[0] += offset[0] * size[0]
                pos[1] += offset[1] * size[1]
                pos[2] += offset[2] * size[2]
                
                # ② オブジェクトのワールド行列を取得して掛け算し、ワールド座標に変換
                # これによってオブジェクトのスケール、回転、平行移動がすべて適用される
                mat = obj.matrix_world
                world_pos = mat @ pos
                
                # 頂点データリストに座標を追加
                vertices["pos"].append([world_pos.x, world_pos.y, world_pos.z])

            # 立方体の12本の辺を構成する頂点のインデックス組み合わせ（各行の start を加算）
            # 前面を構成する辺の頂点インデックス
            indices.append([start + 0, start + 1])
            indices.append([start + 2, start + 3])
            indices.append([start + 0, start + 2])
            indices.append([start + 1, start + 3])
            
            # 奥面を構成する辺の頂点インデックス
            indices.append([start + 4, start + 5])
            indices.append([start + 6, start + 7])
            indices.append([start + 4, start + 6])
            indices.append([start + 5, start + 7])
            
            # 手前と奥を繋ぐ辺の頂点インデックス
            indices.append([start + 0, start + 4])
            indices.append([start + 1, start + 5])
            indices.append([start + 2, start + 6])
            indices.append([start + 3, start + 7])

        # 描画処理
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        batch = gpu_extras.batch.batch_for_shader(shader, "LINES", vertices, indices=indices)
        color = [0.5, 1.0, 1.0, 1.0]
        
        shader.bind()
        shader.uniform_float("color", color)
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
        indent = '\t' * level
        
        self.write_and_print(file, indent + obj.type)
        
        trans, rot, scale = obj.matrix_local.decompose()
        rot = rot.to_euler()

        self.write_and_print(file, indent + "  T %f %f %f" % (trans.x, trans.y, trans.z))
        self.write_and_print(file, indent + "  R %f %f %f" % (math.degrees(rot.x), math.degrees(rot.y), math.degrees(rot.z)))
        self.write_and_print(file, indent + "  S %f %f %f" % (scale.x, scale.y, scale.z))
        
        if "file_name" in obj:
            self.write_and_print(file, indent + "  N %s" % obj["file_name"])

        # 🌟指摘事項に基づき修正：メソッド名、演算子、書き込み処理を修正
        if "collider" in obj:
            self.write_and_print(file, indent + "  C %s" % obj["collider"])
            
            # コライダー中心点の出力
            cc = obj["collider_center"]
            self.write_and_print(file, indent + "  CC %f %f %f" % (cc[0], cc[1], cc[2]))
            
            # コライダーサイズの出力
            cs = obj["collider_size"]
            self.write_and_print(file, indent + "  CS %f %f %f" % (cs[0], cs[1], cs[2]))
            
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

# --- パネルクラス：コライダー ---
class OBJECT_PT_collider(bpy.types.Panel):
    bl_idname = "OBJECT_PT_collider"
    bl_label = "Collider"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        if "collider" in context.object:
            self.layout.prop(context.object, '["collider"]', text="Type")
            self.layout.prop(context.object, '["collider_center"]', text="Center")
            self.layout.prop(context.object, '["collider_size"]', text="Size")
        else:
            self.layout.operator(MYADDON_OT_add_collider.bl_idname, text=MYADDON_OT_add_collider.bl_label)

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
# 目印：MYADDON_OT_add_collider の後ろに不足していたカンマを修正
classes = (
    MYADDON_OT_stretch_vertex,
    MYADDON_OT_create_ico_sphere,
    MYADDON_OT_export_scene,
    MYADDON_OT_add_filename,
    MYADDON_OT_add_collider,
    TOPBAR_MT_my_menu,
    OBJECT_PT_file_name,
    OBJECT_PT_collider,
)

# アドオン有効化時の処理
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR_MT_my_menu.submenu)
    DrawCollider.handle = bpy.types.SpaceView3D.draw_handler_add(DrawCollider.draw_collider, (), "WINDOW", "POST_VIEW")
    print("レベルエディタが有効化されました。")

# アドオン無効化時の処理
def unregister():
    if hasattr(bpy.types, "TOPBAR_MT_editor_menus"):
        try:
            bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR_MT_my_menu.submenu)
            bpy.types.SpaceView3D.draw_handler_remove(DrawCollider.handle, "WINDOW")
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