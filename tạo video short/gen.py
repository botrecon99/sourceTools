import os
import cv2
import numpy as np
import subprocess
from ultralytics import YOLO
from tqdm import tqdm
import assemblyai as aai

# === CẤU HÌNH ===
INPUT_FOLDER = "input/videos"
OUTPUT_FOLDER = "output"
MODEL_PATH = "yolov8n.pt"
API_KEY = "99ea9525425c476c9259e7164bccb2f0"
FRAME_SKIP = 5

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === 1. CẮT VIDEO ===
def cut_video(input_file, start, end, output_file):
    print(f"✂️ Cắt video từ {start} đến {end}...")
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",  # Ẩn log rác
        "-ss", start, "-to", end, "-i", input_file,
        "-c:v", "copy", "-c:a", "copy",
        output_file
    ]
    subprocess.run(cmd)

# === 2. PHÁT HIỆN TÂM NGƯỜI ===
def detect_person_center(video_path, model):
    cap = cv2.VideoCapture(video_path)
    centers = []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    for i in tqdm(range(total_frames), desc="🔍 Phát hiện người"):
        ret, frame = cap.read()
        if not ret:
            break
        if i % FRAME_SKIP != 0:
            continue

        results = model(frame, verbose=False)[0]
        boxes = results.boxes.data.cpu().numpy()
        for box in boxes:
            x1, y1, x2, y2, conf, cls = box
            if int(cls) == 0 and conf > 0.4:
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                centers.append((cx, cy))

    cap.release()
    if centers:
        median_x = int(np.median([c[0] for c in centers]))
        median_y = int(np.median([c[1] for c in centers]))
    else:
        print("⚠️ Không phát hiện người, crop giữa khung hình.")
        median_x, median_y = W // 2, H // 2

    return median_x, median_y, W, H

# === 3. CROP VIDEO ===
def crop_video(input_path, output_path, cx, cy, W, H):
    crop_w, crop_h = 720, 1280
    crop_w = min(W, crop_w)
    crop_h = min(H, crop_h)

    x = max(0, min(W - crop_w, cx - crop_w // 2))
    y = max(0, min(H - crop_h, cy - crop_h // 2))

    crop_filter = f"crop={crop_w}:{crop_h}:{x}:{y}"
    if crop_w < 720 or crop_h < 1280:
        crop_filter += ",scale=720:1280"

    print(f"📐 Crop tại ({x}, {y}) kích thước {crop_w}x{crop_h}")
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", input_path,
        "-vf", crop_filter,
        "-c:v", "libx264", "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd)

# === 4. TẠO PHỤ ĐỀ ===
def generate_subtitles_if_needed(input_file, srt_path, api_key):
    if os.path.exists(srt_path):
        print(f"📄 Phụ đề đã có: {srt_path}")
        return

    print("🧠 Đang transcribe từng từ...")
    aai.settings.api_key = api_key
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(input_file)

    words = transcript.json_response.get("words", [])

    def format_timestamp(ms):
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, word in enumerate(words):
            start = format_timestamp(word["start"])
            end = format_timestamp(word["end"])
            text = word["text"].upper()
            f.write(f"{i+1}\n{start} --> {end}\n{text}\n\n")

    print(f"✅ Đã lưu phụ đề vào: {srt_path}")

# === 5. GHI PHỤ ĐỀ LÊN VIDEO ===
def burn_subtitles(input_path, srt_path, output_path):
    if not os.path.exists(srt_path):
        print("❌ Không có file phụ đề.")
        return

    print("🔥 Ghi phụ đề vào video...")
    srt_path = srt_path.replace("\\", "/")

    if os.path.exists(output_path):
        os.remove(output_path)

    subtitle_filter = (
        f"subtitles='{srt_path}':force_style='"
        "Fontname=Arial Bold,"
        "Fontsize=23,"
        "Alignment=2,"
        "MarginV=50,"
        "WrapStyle=0,"
        "MaxLineCount=1,"
        "BorderStyle=1,"
        "Outline=4,"
        "OutlineColour=&H00000000,"
        "Shadow=0,"
        "PrimaryColour=&H00FFFFFF'"
    )

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", input_path,
        "-vf", subtitle_filter,
        "-c:v", "libx264", "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd)

# === 6. XỬ LÝ TOÀN BỘ VIDEO TRONG FOLDER ===
def process_videos():
    video_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith((".mp4", ".mov", ".avi"))]
    
    for video_file in video_files:
        input_path = os.path.join(INPUT_FOLDER, video_file)
        video_name = os.path.splitext(video_file)[0]
        
        print(f"\n🔥 Đang xử lý video: {video_name}")

        while True: 
            start_time = input(f"Nhập thời gian bắt đầu cho {video_name} (ví dụ: 00:01:10): ")
            end_time = input(f"Nhập thời gian kết thúc cho {video_name} (ví dụ: 00:01:40): ")
            title = input(f"Nhập title cho đoạn video (ví dụ: 03:39–08:35 \"Astrobiology Strategy\"): ")

            final_video_name = f"{title}.mp4"
            temp_clip = os.path.join(OUTPUT_FOLDER, f"{video_name}_clip.mp4")
            cropped_video = os.path.join(OUTPUT_FOLDER, f"{video_name}_cropped.mp4")
            final_video = os.path.join(OUTPUT_FOLDER, final_video_name)
            srt_file = os.path.join(OUTPUT_FOLDER, f"{video_name}.srt")

            cut_video(input_path, start_time, end_time, temp_clip)

            model = YOLO(MODEL_PATH)
            cx, cy, W, H = detect_person_center(temp_clip, model)
            crop_video(temp_clip, cropped_video, cx, cy, W, H)

            if not os.path.exists(cropped_video):
                print("❌ Crop thất bại.")
                continue

            generate_subtitles_if_needed(cropped_video, srt_file, API_KEY)

            if os.path.exists(srt_file):
                burn_subtitles(cropped_video, srt_file, final_video)
                print(f"✅ Hoàn tất video: {final_video}")
            else:
                print("⚠️ Không có phụ đề. Xuất video crop.")
                os.rename(cropped_video, final_video)

            # Xoá file tạm
            for f in [temp_clip, cropped_video, srt_file]:
                if os.path.exists(f):
                    os.remove(f)

            next_clip = input("Có muốn cắt đoạn khác từ video này không? (Y/N): ").strip().lower()
            if next_clip != 'y':
                print("Chuyển sang video tiếp theo...\n")
                break

if __name__ == "__main__":
    process_videos()
