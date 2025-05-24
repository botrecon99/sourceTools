import pyautogui
import keyboard
import time

print("Chờ bạn nhấn Shift+F1 để bắt đầu lấy tọa độ chuột...")

keyboard.wait('shift+f1')
print("Bắt đầu in tọa độ chuột, nhấn ESC để dừng.")

try:
    while True:
        x, y = pyautogui.position()
        print(f"Chuột đang ở: {x}, {y}")
        time.sleep(1)

        if keyboard.is_pressed('esc'):
            print("Đã dừng lấy tọa độ.")
            break

except KeyboardInterrupt:
    print("Dừng bằng Ctrl+C")
