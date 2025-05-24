import os
import subprocess
from config import INPUT_FOLDER, OUTPUT_FOLDER

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def convert_with_nvenc(input_video, output_video):
    command = [
        'ffmpeg', '-y', '-hwaccel', 'cuda', '-i', input_video,
        '-vf', 'fps=30',             # Chỉ chỉnh FPS (giữ nguyên độ phân giải)
        '-c:v', 'h264_nvenc',        # Sử dụng GPU NVIDIA để mã hóa
        '-preset', 'p4',             # Cân bằng giữa tốc độ và chất lượng (p1=nhanh nhất, p7=chậm nhất)
        '-rc', 'vbr',                # Rate control mode: Variable Bitrate
        '-cq', '19',                 # Chất lượng (CQ thấp hơn = chất lượng cao hơn)
        '-b:v', '0',                 # Bắt buộc khi dùng CQ
        '-c:a', 'aac',               # Âm thanh
        '-ar', '44100',
        output_video
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

video_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))]

if not video_files:
    print("❌ Không có video nào trong thư mục input.")
    exit()

for video in video_files:
    input_video = os.path.join(INPUT_FOLDER, video)
    output_video = os.path.join(OUTPUT_FOLDER, video)
    
    print(f"🚀 GPU đang xử lý video: {input_video}")
    convert_with_nvenc(input_video, output_video)
    print(f"✅ Xong: {output_video}")

print("🎬 Hoàn tất – Dùng GPU RTX 3060 để mã hóa video nhanh chóng.")
