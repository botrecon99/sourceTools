import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# === Cấu hình tùy chỉnh ===
SECONDS_TO_CUT_FROM_START = 0
MAX_WORKERS = 4  # Số luồng xử lý song song

def get_video_duration(video_path):
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        return float(result.stdout)
    except ValueError:
        return 0

def process_video(video_path, output_folder):
    basename = os.path.basename(video_path)
    name, ext = os.path.splitext(basename)

    print(f"[10%] Đang lấy độ dài video: {basename}")
    duration = get_video_duration(video_path)
    if duration <= 0:
        print(f"[LỖI] Không thể đọc độ dài video: {basename}")
        return

    SECONDS_TO_CUT_FROM_END = 600 if duration > 90 * 60 else 300
    final_duration = max(duration - SECONDS_TO_CUT_FROM_START - SECONDS_TO_CUT_FROM_END, 1)
    output_path = os.path.join(output_folder, f"{name}{ext}")

    print(f"[90%] Đang cắt và lưu video (dùng GPU)... {basename}")
    command = [
        'ffmpeg', '-y',
        '-hwaccel', 'cuda',  # Dùng CUDA nếu cần giải mã bằng GPU
        '-i', video_path,
        '-ss', str(SECONDS_TO_CUT_FROM_START),
        '-t', str(int(final_duration)),
        '-c:v', 'h264_nvenc',          # Bộ mã hóa GPU NVIDIA
        '-preset', 'fast',             # preset GPU (fast/good/slow, v.v.)
        '-cq', '23',                   # Độ nén tương tự CRF (chất lượng)
        '-c:a', 'aac',
        '-b:a', '128k',
        '-threads', '2',
        '-avoid_negative_ts', 'make_zero',
        output_path
    ]

    try:
        subprocess.run(command, check=True)
        print(f"[100%] ✅ {basename} → còn lại {final_duration:.2f}s, lưu tại {output_path}")
    except subprocess.CalledProcessError:
        print(f"[LỖI] Không thể xử lý video: {basename}")

# === Thư mục input/output ===
input_folder = "videos_input"
output_folder = "videos_output"
os.makedirs(output_folder, exist_ok=True)

# === Lấy danh sách video ===
video_files = [
    os.path.join(input_folder, f)
    for f in os.listdir(input_folder)
    if f.lower().endswith((".mp4", ".mkv", ".avi", ".mov"))
]

# === Đa luồng xử lý ===
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(process_video, video_path, output_folder) for video_path in video_files]
    for future in as_completed(futures):
        pass  # xử lý xong từng video
