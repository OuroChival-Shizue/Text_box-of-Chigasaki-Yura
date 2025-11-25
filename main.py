print("""
快捷键说明:
Alt+1-9: 切换表情1-9（若该表情不存在则无效）
Enter: 生成图片
Esc: 退出程序
Ctrl+Tab: 清除预生成图片

说明：
首次运行会预生成立绘+背景的组合图片，可能需要等待几秒。
之后按 Enter 就可以把当前输入框里的文本生成对话框图片并发出去。
""")


# ================= 全局配置 =================
mahoshojo_postion = [521, 570]
mahoshojo_over    = [1760, 740]
NAME_POSITION  = (690, 480)
NAME_FONT_SIZE = 42
NAME_COLOR     = (0, 0, 0)
import random
import time
import keyboard
import pyperclip
import io
from PIL import Image
import win32clipboard
import os
import shutil
import getpass

from text_fit_draw import draw_text_auto
from image_fit_paste import paste_image_auto

# 文本框背景（蓝条+白色气泡）的图片路径
TEXTBOX_BG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textbox_bg.png")

# 当前只有一个角色：茅崎夕樱
CHAR_NAME = "yuraa"
EMOTION_COUNT = 7          # 茅崎夕樱的表情数量（表情图片数量）
FONT_FILE = "LXGWWenKai-Medium.ttf"    # 对话字体

# 表情选择相关
value_1   = -1             # 上一次实际使用的图片编号
expression = None          # Alt+数字指定的表情索引（1~9）

# ================= 文字配置：角色名 =================

# 角色文字配置字典
text_configs_dict = {
    "yuraa": [
        {
            "text": "茅崎夕樱",
            "position": NAME_POSITION,
            "font_color": (253, 145, 175),
            "font_size": NAME_FONT_SIZE
        },
        # 下面三个是占位空项，不绘制任何东西
        {"text": "", "position": (0, 0), "font_color": NAME_COLOR, "font_size": 1},
        {"text": "", "position": (0, 0), "font_color": NAME_COLOR, "font_size": 1},
        {"text": "", "position": (0, 0), "font_color": NAME_COLOR, "font_size": 1},
    ]
}
# 获取当前用户名
username = getpass.getuser()

# 用户文档路径
if os.name == 'nt':  # Windows
    user_documents = os.path.join('C:\\', 'Users', username, 'Documents')
else:
    user_documents = os.path.expanduser('~/Documents')

magic_cut_folder = os.path.join(user_documents, '夕樱')
os.makedirs(magic_cut_folder, exist_ok=True)

# ================= 工具函数 =================

def get_current_character():
    # 单角色版，永远返回 yuraa
    return CHAR_NAME

def get_current_font():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), FONT_FILE)

def get_current_emotion_count():
    return EMOTION_COUNT

def delate(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.jpg'):
            os.remove(os.path.join(folder_path, filename))

def generate_and_save_images(character_name: str):
    now_file = os.path.dirname(os.path.abspath(__file__))

    emotion_count = get_current_emotion_count()

    # 已经生成过就不用再来一次
    for filename in os.listdir(magic_cut_folder):
        if filename.startswith(character_name):
            return

    print("正在预生成图片，请稍候……")

    # 预先加载文本框背景
    textbox_bg = None
    if os.path.exists(TEXTBOX_BG_PATH):
        textbox_bg = Image.open(TEXTBOX_BG_PATH).convert("RGBA")

    for i in range(16):
        for j in range(emotion_count):
            background_path = os.path.join(now_file, "background", f"c{i+1}.png")
            overlay_path    = os.path.join(now_file, character_name, f"{character_name} ({j+1}).png")

            background = Image.open(background_path).convert("RGBA")
            overlay    = Image.open(overlay_path).convert("RGBA")

            img_num = j * 16 + i + 1
            result  = background.copy()

            # 先贴文本框在最底下
            bg_w, bg_h = result.size
            if textbox_bg is not None:
                tb_w, tb_h = textbox_bg.size
                x = (bg_w - tb_w) // 2
                y = bg_h - tb_h
                result.paste(textbox_bg, (x, y), textbox_bg)

            # 缩放立绘到最大边约 550 像素
            TARGET_SIZE = 550
            ow, oh = overlay.size
            scale = TARGET_SIZE / max(ow, oh)
            new_w = int(ow * scale)
            new_h = int(oh * scale)
            overlay = overlay.resize((new_w, new_h), Image.LANCZOS)

            # 固定立绘位置
            char_x = 0
            char_y = 260
            result.paste(overlay, (char_x, char_y), overlay)

            save_path = os.path.join(magic_cut_folder, f"{character_name} ({img_num}).jpg")
            result.convert("RGB").save(save_path)

    print("预生成完成")

# 预生成一次
generate_and_save_images(get_current_character())

def get_expression(i: int):
    """Alt+数字选择表情索引（1~9）"""
    global expression
    if 1 <= i <= get_current_emotion_count():
        print(f"已切换至第 {i} 个表情")
        expression = i

def get_random_value():
    """随机选择一张图片，同时尽量避免和上次同一表情"""
    global value_1, expression
    character_name = get_current_character()
    emotion_count  = get_current_emotion_count()
    total_images   = 16 * emotion_count

    # 指定表情优先
    if expression:
        i = random.randint((expression - 1) * 16 + 1, expression * 16)
        value_1 = i
        expression = None
        return f"{character_name} ({i})"

    max_attempts = 100
    attempts = 0

    while attempts < max_attempts:
        i = random.randint(1, total_images)
        current_emotion = (i - 1) // 16

        if value_1 == -1:
            value_1 = i
            return f"{character_name} ({i})"

        if current_emotion != (value_1 - 1) // 16:
            value_1 = i
            return f"{character_name} ({i})"

        attempts += 1

    value_1 = i
    return f"{character_name} ({i})"

# ================= 剪贴板相关 =================

def copy_png_bytes_to_clipboard(png_bytes: bytes):
    image = Image.open(io.BytesIO(png_bytes))
    with io.BytesIO() as output:
        image.convert("RGB").save(output, "BMP")
        bmp_data = output.getvalue()[14:]
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
    win32clipboard.CloseClipboard()

def cut_all_and_get_text() -> str:
    """Ctrl+A + Ctrl+X 剪切全部文本，并返回文本内容"""
    pyperclip.copy("")
    keyboard.send("ctrl+a")
    keyboard.send("ctrl+x")
    time.sleep(0.1)
    return pyperclip.paste()

def try_get_image() -> Image.Image | None:
    """尝试从剪贴板获取图片"""
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            if data:
                bmp_data = data
                header = b'BM' + (len(bmp_data) + 14).to_bytes(4, 'little') \
                         + b'\x00\x00\x00\x00\x36\x00\x00\x00'
                image = Image.open(io.BytesIO(header + bmp_data))
                return image
    except Exception as e:
        print("无法从剪贴板获取图像：", e)
    finally:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
    return None

# ================= 主逻辑 =================

HOTKEY             = "enter"
SELECT_ALL_HOTKEY  = "ctrl+a"
CUT_HOTKEY         = "ctrl+x"
PASTE_HOTKEY       = "ctrl+v"
SEND_HOTKEY        = "enter"
BLOCK_HOTKEY       = False
DELAY              = 0.1
AUTO_PASTE_IMAGE   = True
AUTO_SEND_IMAGE    = True

def Start():
    print("Start generate...")

    character_name = get_current_character()
    address = os.path.join(magic_cut_folder, get_random_value() + ".jpg")
    BASEIMAGE_FILE = address
    print(character_name, "使用图片：", BASEIMAGE_FILE)

    base_img = Image.open(BASEIMAGE_FILE).convert("RGBA")

    TEXT_BOX_TOPLEFT     = (mahoshojo_postion[0], mahoshojo_postion[1])
    IMAGE_BOX_BOTTOMRIGHT = (mahoshojo_over[0], mahoshojo_over[1])

    text  = cut_all_and_get_text()
    image = try_get_image()

    if text == "" and image is None:
        print("no text or image")
        return

    png_bytes = None

    if image is not None:
        try:
            print("Get image")
            png_bytes = paste_image_auto(
                image_source=base_img,
                image_overlay=None,
                top_left=TEXT_BOX_TOPLEFT,
                bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                content_image=image,
                align="center",
                valign="middle",
                padding=12,
                allow_upscale=True,
                keep_alpha=True,
                role_name=character_name,
                text_configs_dict=text_configs_dict,
            )
        except Exception as e:
            print("Generate image failed:", e)
            return

    elif text != "":
        print("Get text:", text)
        display_text = text.strip()
        if display_text and not (display_text.startswith("「") and display_text.endswith("」")):
            display_text = f"「{display_text}」"

        try:
            png_bytes = draw_text_auto(
                image_source=base_img,
                image_overlay=None,
                top_left=TEXT_BOX_TOPLEFT,
                bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                text=display_text,
                align="left",
                valign="top",
                color=(255, 255, 255),
                max_font_height=55,
                font_path=get_current_font(),
                role_name=character_name,
                text_configs_dict=text_configs_dict,
            )
        except Exception as e:
            print("Generate image failed:", e)
            return

    if png_bytes is None:
        print("Generate image failed!")
        return

    copy_png_bytes_to_clipboard(png_bytes)

    if AUTO_PASTE_IMAGE:
        keyboard.send(PASTE_HOTKEY)
        time.sleep(0.3)
        if AUTO_SEND_IMAGE:
            keyboard.send(SEND_HOTKEY)

for i in range(1, 10):
    keyboard.add_hotkey(f'alt+{i}', lambda idx=i: get_expression(idx))

keyboard.add_hotkey('ctrl+Tab', lambda: delate(magic_cut_folder))

ok = keyboard.add_hotkey(HOTKEY, Start, suppress=BLOCK_HOTKEY or HOTKEY == SEND_HOTKEY)

keyboard.wait("Esc")
