import os
import math
import subprocess

# === Cấu hình ===
INPUT_FOLDER = "videos_input"
OUTPUT_FOLDER = "videos_output"
CLIP_DURATION = 120  # thời lượng mỗi đoạn (giây)

# Tạo thư mục đầu ra nếu chưa có
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Lấy danh sách file video hợp lệ
video_files = [
    f for f in os.listdir(INPUT_FOLDER)
    if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))
]

if not video_files:
    raise FileNotFoundError("❌ Không tìm thấy video nào trong thư mục 'videos_input'.")

def get_video_duration(video_path):
    """Lấy độ dài video (giây)"""
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        return float(result.stdout.strip())
    except:
        return 0

def cut_video_with_ffmpeg(input_path, output_path, start_time, duration):
    """Dùng GPU (NVENC) để cắt video"""
    command = [
        'ffmpeg', '-y',
        '-ss', str(start_time),
        '-t', str(duration),
        '-i', input_path,
        '-c:v', 'h264_nvenc',
        '-preset', 'fast',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-avoid_negative_ts', 'make_zero',
        output_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# === Xử lý từng video ===
for video_file in video_files:
    input_path = os.path.join(INPUT_FOLDER, video_file)
    base_name = os.path.splitext(video_file)[0]

    print(f"\n▶ Đang xử lý: {video_file}")
    duration = get_video_duration(input_path)

    if duration < CLIP_DURATION:
        print(f"⚠️ Video quá ngắn (< {CLIP_DURATION}s), bỏ qua.")
        continue

    num_parts = math.ceil(duration / CLIP_DURATION)
    for i in range(num_parts):
        start_time = i * CLIP_DURATION
        clip_len = min(CLIP_DURATION, duration - start_time)

        output_name = f"{base_name}_part_{i+1:02d}.mp4"
        output_path = os.path.join(OUTPUT_FOLDER, output_name)

        print(f"  ⏳ Cắt đoạn {i+1}/{num_parts}: {start_time}s → {start_time+clip_len}s")
        cut_video_with_ffmpeg(input_path, output_path, start_time, clip_len)

    print(f"✅ Hoàn tất: {video_file}")

print("\n🎉 Đã xử lý xong tất cả video!")
