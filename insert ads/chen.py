import ctypes
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Chạy lại chính script này với quyền admin
    print("Chưa chạy quyền admin, sẽ khởi động lại với quyền admin...")
    params = ' '.join([f'"{x}"' for x in sys.argv])
    # Sử dụng ShellExecuteEx với 'runas' để chạy quyền admin
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit()

# Phần code chính bắt đầu ở đây
import pyautogui
import time
import keyboard  # pip install keyboard

def format_time(total_seconds):
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    frames = 0
    return f"{hours}:{minutes:02d}:{seconds:02d}:{frames:02d}"

button_x, button_y = 371, 296
input_x, input_y = 977, 350

# Nhập lựa chọn đơn vị thời gian
while True:
    unit = input("Bạn muốn chèn quảng cáo cách nhau bao nhiêu phút (p) hay giây (s)? (p/s): ").strip().lower()
    if unit in ['p', 's']:
        break
    print("Vui lòng nhập 'p' hoặc 's'.")

# Nhập số bước nhảy (số phút hoặc số giây)
while True:
    try:
        step = int(input(f"Nhập số {'phút' if unit == 'p' else 'giây'} mỗi lần chèn quảng cáo: "))
        if step > 0:
            break
        else:
            print("Phải nhập số nguyên dương.")
    except:
        print("Vui lòng nhập số nguyên hợp lệ.")

print("Chờ nhấn Shift + F1 để bắt đầu...")
keyboard.wait('shift+f1')

print("Bắt đầu chèn quảng cáo...")

i = 1
while True:
    if keyboard.is_pressed('shift+f2'):
        print("Đã nhận lệnh dừng (Shift + F2). Kết thúc chương trình.")
        break

    pyautogui.click(button_x, button_y)
    # time.sleep(1)

    pyautogui.click(input_x, input_y)
    # time.sleep(0.5)

    # Xóa hết nội dung trong ô input (Ctrl + A rồi Delete)
    pyautogui.hotkey('ctrl', 'a')
    # time.sleep(0.2)
    pyautogui.press('delete')
    # time.sleep(0.2)

    # Tính tổng giây theo lựa chọn đơn vị
    if unit == 'p':
        total_seconds = i * step * 60
    else:
        total_seconds = i * step

    time_str = format_time(total_seconds)
    pyautogui.typewrite(time_str)

    pyautogui.press('enter')
    print(f"Đã chèn quảng cáo tại {time_str}")

    i += 1
    # time.sleep(1.5)

print("Chương trình kết thúc.")
