import os
import subprocess
from config import INPUT_FOLDER, OUTPUT_FOLDER

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def convert_with_nvenc(input_video, output_video):
    command = [
        'ffmpeg', '-y', '-hwaccel', 'cuda', '-i', input_video,
        '-vf', 'fps=30',
        '-c:v', 'h264_nvenc',
        '-preset', 'p4',
        '-rc', 'vbr',
        '-cq', '19',
        '-b:v', '0',
        '-c:a', 'aac',
        '-ar', '44100',
        output_video
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Tìm toàn bộ video trong thư mục con
video_files = []
for root, _, files in os.walk(INPUT_FOLDER):
    for file in files:
        if file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            full_input_path = os.path.join(root, file)
            video_files.append(full_input_path)

if not video_files:
    print("❌ Không có video nào trong thư mục input hoặc các thư mục con.")
    exit()

for input_video in video_files:
    # Lấy đường dẫn tương đối từ INPUT_FOLDER
    relative_path = os.path.relpath(input_video, INPUT_FOLDER)
    output_video = os.path.join(OUTPUT_FOLDER, relative_path)

    # Tạo thư mục con nếu cần
    os.makedirs(os.path.dirname(output_video), exist_ok=True)

    print(f"🚀 GPU đang xử lý video: {input_video}")
    convert_with_nvenc(input_video, output_video)
    print(f"✅ Xong: {output_video}")

print("🎬 Hoàn tất – Đã mã hóa toàn bộ video với cấu trúc thư mục giữ nguyên.")
