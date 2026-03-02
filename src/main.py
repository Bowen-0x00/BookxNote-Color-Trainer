import pymem
import keyboard
import tkinter as tk
import threading

# ================= i18n Dictionary =================
# Stores UI text for multiple languages
LANGUAGES = {
    "en": {
        "title": "🎨 BookxNote Color Switcher",
        "status_wait": "Status: Waiting for connection...",
        "status_ok": "Status: 🟢 Connected to {exe}",
        "status_err": "Status: 🔴 {exe} not found. Please open it.",
        "btn_reconnect": "🔄 Manual Reconnect",
        "btn_lang": "🌐 切换为中文",
        "hk_title": "Global Hotkeys:",
        "log_ready": "Log: Ready",
        "log_ok": "Log: Successfully switched to {color}!",
        "log_err_write": "Log: Write failed ({err})",
        "log_err_mem": "Log: Valid memory address not found",
        "c1": "[F1] - Light Blue",
        "c2": "[F2] - Soft Red",
        "c3": "[F3] - Mint Green",
        "c4": "[F4] - Neon Yellow"
    },
    "zh": {
        "title": "🎨 BookxNote 快捷换色器",
        "status_wait": "状态: 等待连接...",
        "status_ok": "状态: 🟢 成功连接到 {exe}",
        "status_err": "状态: 🔴 未找到 {exe}，请先打开软件",
        "btn_reconnect": "🔄 手动重新连接",
        "btn_lang": "🌐 Switch to English",
        "hk_title": "已绑定全局快捷键:",
        "log_ready": "日志: 准备就绪",
        "log_ok": "日志: 成功切换为 {color}!",
        "log_err_write": "日志: 写入失败 ({err})",
        "log_err_mem": "日志: 找不到有效内存地址",
        "c1": "[F1] - 浅蓝",
        "c2": "[F2] - 柔红",
        "c3": "[F3] - 薄荷绿",
        "c4": "[F4] - 荧光黄"
    }
}

current_lang = "en" # Default language

# ================= Color Conversion Utility =================
def hex_to_8byte_color(hex_str, alpha="FF"):
    """
    Converts standard web color (#RRGGBB) to BookxNote's 8-byte memory format (BBGGRRFF).
    Example: "#59C6FF" -> 0xFFFFC6C65959FFFF
    """
    hex_str = hex_str.lstrip('#').upper()
    if len(hex_str) == 6:
        r, g, b, a = hex_str[0:2], hex_str[2:4], hex_str[4:6], alpha
    else:
        r, g, b, a = "00", "00", "00", "FF" # Fallback to black
    
    # Double the 8-bit channels to 16-bit and arrange as BB GG RR FF
    return int(f"{b+b}{g+g}{r+r}{a+a}", 16)

# ================= Core Configuration =================
PROCESS_NAME = "BookxNotePro.exe"

# Static base offsets (Multiple fallbacks for stability)
STATIC_BASE_OFFSETS = [0x00E48710, 0x00E48748, 0x00E487D8, 0x00E487E0]

# Pointer offset chain (Read from bottom to top in Cheat Engine)
OFFSETS = [0x8, 0x38, 0x18, 0x5E8, 0x30, 0xE8, 0x4C]

# 🎨 Preset Colors (Using standard Hex codes)
COLORS = {
    "F1": hex_to_8byte_color("#59C6FF"), 
    "F2": hex_to_8byte_color("#FF6B6B"), 
    "F3": hex_to_8byte_color("#4ECDC4"), 
    "F4": hex_to_8byte_color("#FFE66D")  
}
# ====================================================

pm = None

def attach_process():
    """Attempt to attach to the target process."""
    global pm
    txt = LANGUAGES[current_lang]
    try:
        pm = pymem.Pymem(PROCESS_NAME)
        lbl_status.config(text=txt["status_ok"].format(exe=PROCESS_NAME), fg="green")
        return True
    except pymem.exception.ProcessNotFound:
        lbl_status.config(text=txt["status_err"].format(exe=PROCESS_NAME), fg="red")
        pm = None
        return False

def get_final_address():
    """Resolve the multi-level pointer chain with automatic fallback."""
    if not pm: return None
    try:
        module_base = pymem.process.module_from_name(pm.process_handle, PROCESS_NAME).lpBaseOfDll
    except Exception:
        return None

    # Iterate through possible base offsets
    for base_offset in STATIC_BASE_OFFSETS:
        try:
            addr = pm.read_longlong(module_base + base_offset)
            if addr == 0: continue
                
            # Traverse the offset chain
            for offset in OFFSETS[:-1]:
                addr = pm.read_longlong(addr + offset)
                if addr == 0: break
            
            # Add the final offset
            if addr != 0: return addr + OFFSETS[-1]
        except Exception:
            continue
    return None

def change_color(color_hex, color_key):
    """Write the new color value to memory and update UI."""
    if not pm and not attach_process(): return
    
    txt = LANGUAGES[current_lang]
    final_addr = get_final_address()
    
    if final_addr:
        try:
            pm.write_ulonglong(final_addr, color_hex)
            lbl_log.config(text=txt["log_ok"].format(color=txt[color_key]), fg="blue")
        except Exception as e:
            lbl_log.config(text=txt["log_err_write"].format(err=e), fg="red")
    else:
        lbl_log.config(text=txt["log_err_mem"], fg="red")

def start_hotkey_listener():
    """Listen for global hotkeys in a background thread."""
    keyboard.add_hotkey('F1', lambda: change_color(COLORS["F1"], "c1"))
    keyboard.add_hotkey('F2', lambda: change_color(COLORS["F2"], "c2"))
    keyboard.add_hotkey('F3', lambda: change_color(COLORS["F3"], "c3"))
    keyboard.add_hotkey('F4', lambda: change_color(COLORS["F4"], "c4"))
    keyboard.wait()

def toggle_language():
    """Switch between English and Chinese UI."""
    global current_lang
    current_lang = "zh" if current_lang == "en" else "en"
    update_ui_text()

def update_ui_text():
    """Refresh all UI elements with the current language dictionary."""
    txt = LANGUAGES[current_lang]
    root.title(txt["title"])
    lbl_title.config(text=txt["title"])
    btn_reconnect.config(text=txt["btn_reconnect"])
    btn_lang.config(text=txt["btn_lang"])
    lbl_hk_title.config(text=txt["hk_title"])
    lbl_c1.config(text=txt["c1"])
    lbl_c2.config(text=txt["c2"])
    lbl_c3.config(text=txt["c3"])
    lbl_c4.config(text=txt["c4"])
    
    if pm:
        lbl_status.config(text=txt["status_ok"].format(exe=PROCESS_NAME))
    else:
        lbl_status.config(text=txt["status_wait"])

# ================= UI Construction =================
root = tk.Tk()
root.geometry("360x320")
root.attributes("-topmost", True) # Keep window on top

# Top Bar (Title & Lang Toggle)
top_frame = tk.Frame(root)
top_frame.pack(fill="x", pady=5, padx=10)
btn_lang = tk.Button(top_frame, command=toggle_language, font=("Arial", 8), relief="flat", cursor="hand2")
btn_lang.pack(side="right")

lbl_title = tk.Label(root, font=("Arial", 14, "bold"))
lbl_title.pack(pady=5)

lbl_status = tk.Label(root, fg="orange", font=("Arial", 10))
lbl_status.pack(pady=5)

btn_reconnect = tk.Button(root, command=attach_process, width=20, font=("Arial", 9))
btn_reconnect.pack(pady=5)

# Hotkeys Info Frame
info_frame = tk.Frame(root)
info_frame.pack(pady=10)
lbl_hk_title = tk.Label(info_frame, font=("Arial", 10, "bold"))
lbl_hk_title.grid(row=0, column=0, sticky="w", columnspan=2, pady=5)

lbl_c1 = tk.Label(info_frame)
lbl_c1.grid(row=1, column=0, sticky="w", padx=15)
lbl_c2 = tk.Label(info_frame)
lbl_c2.grid(row=2, column=0, sticky="w", padx=15)
lbl_c3 = tk.Label(info_frame)
lbl_c3.grid(row=1, column=1, sticky="w", padx=15)
lbl_c4 = tk.Label(info_frame)
lbl_c4.grid(row=2, column=1, sticky="w", padx=15)

lbl_log = tk.Label(root, fg="gray", font=("Arial", 9))
lbl_log.pack(side="bottom", pady=10)

# Initialize UI text
update_ui_text()

# Start background threads
threading.Thread(target=start_hotkey_listener, daemon=True).start()
root.after(500, attach_process)

root.mainloop()
