import bpy

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

# アドオン有効化時の処理
def register():
    # クラスの登録
    for cls in classes:
        bpy.utils.register_class(cls)
    # トップバーのメニューにサブメニューを追加
    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR_MT_my_menu.submenu)
    print("レベルエディタが有効化されました。")

# アドオン無効化時の処理
def unregister():
    # トップバーのメニューからサブメニューを削除
    try:
        bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR_MT_my_menu.submenu)
    except:
        pass
    # クラスの登録解除
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
    print("レベルエディタが無効化されました。")
    
# トップバーの拡張メニュー定義クラス
class TOPBAR_MT_my_menu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_my_menu"
    bl_label = "MyMenu"
    bl_description = "拡張メニュー by " + bl_info["author"]

    # メニュー内の描画設定
    def draw(self, context):
        self.layout.operator("wm.url_open_preset", text="Manual", icon='HELP')

    # サブメニューの追加処理
    def submenu(self, context):
        self.layout.menu(TOPBAR_MT_my_menu.bl_idname)

# 登録対象のクラス一覧
classes = (TOPBAR_MT_my_menu,)

# スクリプト直接実行時の処理
if __name__ == "__main__":
    register()