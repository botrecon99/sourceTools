import os
import subprocess
import logging
import re
from datetime import timedelta
from PIL import Image  # Dùng để resize ảnh nhanh

# === Setup Logger ===
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

file_handler = logging.FileHandler('processing.log', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# === Paths ===
input_folder = 'input_audios'
background_image = 'background.jpg'
temp_image = 'background_resized.jpg'  # Ảnh đã resize xuống 854x480
output_folder = 'output_videos'
os.makedirs(output_folder, exist_ok=True)

grain_video = 'grain_overlay_fixed.mp4'  # Đặt tên file video grain overlay của bạn ở đây
people_image = 'people.png'

# === Resize ảnh về 854x480
def resize_background(input_image, output_image, target_width=854, target_height=480):
    img = Image.open(input_image)
    img = img.resize((target_width, target_height), Image.LANCZOS)
    img.save(output_image)
    logger.info(f"📷 Đã resize ảnh nền: {output_image} ({target_width}x{target_height})")

# === Clean filename (remove special characters)
def clean_filename(name):
    name = re.sub(r'[^\w\s-]', '', name)  # Xóa ký tự đặc biệt
    name = re.sub(r'\s+', ' ', name).strip()  # Xóa khoảng trắng thừa
    return name

# === Get audio duration (seconds)
def get_audio_duration(file_path):
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        return float(result.stdout)
    except ValueError:
        return 0

# === Step: Ghép background + audio + grain overlay thành video
def create_video_from_audio(audio_file, image_file, output_video, duration):
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', image_file,         # 0: background
        '-stream_loop', '-1',
        '-i', grain_video,        # 1: grain overlay
        '-loop', '1',
        '-i', people_image,       # 2: people image
        '-i', audio_file,         # 3: audio
        '-r', '25',
        '-filter_complex',
        "[1:v]format=yuva420p,colorchannelmixer=aa=0.3[grain];"
        "[0:v][grain]overlay=0:0[tmpbg];"
        "[2:v]scale=854:480[people];"
        "[tmpbg][people]overlay=x='W/2-w/2+10*sin(2*PI*t/2)':y=H-h+5*sin(2*PI*t/3)[outv]",
        '-map', '[outv]',
        '-map', '3:a:0',
        '-c:v', 'h264_nvenc',
        '-preset', 'p1',
        '-rc', 'constqp',
        '-qp', '28',
        '-c:a', 'copy',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        '-t', str(duration),
        output_video
    ]
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("[INFO] GPU encode failed, switching to CPU (libx264)...")
        logger.warning("GPU encode failed, switching to CPU (libx264)...")
        ffmpeg_cmd_cpu = ffmpeg_cmd.copy()
        idx = ffmpeg_cmd_cpu.index('-c:v')
        ffmpeg_cmd_cpu[idx+1] = 'libx264'
        if '-rc' in ffmpeg_cmd_cpu:
            rc_idx = ffmpeg_cmd_cpu.index('-rc')
            del ffmpeg_cmd_cpu[rc_idx:rc_idx+2]
        if '-preset' in ffmpeg_cmd_cpu:
            preset_idx = ffmpeg_cmd_cpu.index('-preset')
            ffmpeg_cmd_cpu[preset_idx+1] = 'veryfast'
        if '-qp' in ffmpeg_cmd_cpu:
            qp_idx = ffmpeg_cmd_cpu.index('-qp')
            del ffmpeg_cmd_cpu[qp_idx:qp_idx+2]
        result_cpu = subprocess.run(ffmpeg_cmd_cpu, capture_output=True, text=True)
        print(result_cpu.stderr)
        result_cpu.check_returncode()
    else:
        print(result.stderr)
        result.check_returncode()

# === Main Process
def process_all():
    # Resize ảnh background về 854x480 trước khi bắt đầu
    resize_background(background_image, temp_image)

    mp3_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith('.mp3')])

    if not mp3_files:
        logger.error("⚠️ Không tìm thấy file mp3.")
        return

    for filename in mp3_files:
        filepath = os.path.join(input_folder, filename)
        duration = get_audio_duration(filepath)

        # Clean tên file đầu ra
        safe_filename = clean_filename(os.path.splitext(filename)[0])
        output_video_path = os.path.join(output_folder, safe_filename + '.mp4')

        logger.info(f"🎵 Đang xử lý: {filename}")

        create_video_from_audio(filepath, temp_image, output_video_path, duration)

        logger.info(f"✅ Xong: {filename}")

if __name__ == "__main__":
    process_all()
