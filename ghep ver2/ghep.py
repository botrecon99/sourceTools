import os
import random
import subprocess
import shutil
from config import INPUT_FOLDER, OUTPUT_FOLDER, LOG_FOLDER

MIN_DURATION = 3300  # 55 phút
MAX_DURATION = 4200  # 70 phút
TEMP_FOLDER = "temp_ffmpeg_safe"
PRE_MERGED_FOLDER = "pre_merged"

# Tạo thư mục nếu chưa có
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(PRE_MERGED_FOLDER, exist_ok=True)

def get_video_duration(video_path):
    try:
        duration_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ]
        return float(subprocess.check_output(duration_cmd).decode().strip())
    except subprocess.CalledProcessError:
        print(f"⚠ Lỗi khi đọc file: {video_path}")
        return None

def escape_path(path):
    # Escape ký tự đặc biệt (đặc biệt là dấu ' trong ffmpeg)
    return path.replace("\\", "/").replace("'", "'\\''")

# Bước 1: Ghép các "con" trong từng thư mục con → thành 1 "bố"
merged_videos = []
for root, _, files in os.walk(INPUT_FOLDER):
    mp4_files = [f for f in files if f.lower().endswith(".mp4")]
    if not mp4_files:
        continue

    con_paths = [os.path.join(root, f) for f in mp4_files]
    random.shuffle(con_paths)

    merged_name = os.path.basename(root).strip().replace(" ", "_") + ".mp4"
    merged_path = os.path.join(PRE_MERGED_FOLDER, merged_name)

    if len(con_paths) == 1:
        shutil.copy2(con_paths[0], merged_path)
        merged_videos.append(merged_path)
        continue

    mylist_path = os.path.join(TEMP_FOLDER, "mylist_folder.txt")
    with open(mylist_path, "w", encoding="utf-8") as f:
        for path in con_paths:
            abs_path = escape_path(os.path.abspath(path))
            f.write(f"file '{abs_path}'\n")

    try:
        subprocess.run([
            "ffmpeg", "-f", "concat", "-safe", "0", "-i", mylist_path,
            "-c", "copy", merged_path
        ], check=True)
        merged_videos.append(merged_path)
        print(f"✅ Ghép bố từ: {root} → {merged_name}")
    except subprocess.CalledProcessError:
        print(f"❌ Lỗi khi ghép các video trong thư mục: {root}")

# Bước 2: Ghép các "bố" thành video chính
video_files = merged_videos.copy()
random.shuffle(video_files)

if not video_files:
    print("❌ Không có video nào sau khi ghép từ các thư mục con.")
    exit()

used_first_videos = set()

for first_video in video_files:
    if first_video in used_first_videos:
        continue

    first_duration = get_video_duration(first_video)
    if first_duration is None:
        continue

    selected_videos = [first_video]
    total_duration = int(first_duration)
    temp_video_files = video_files.copy()

    while total_duration < MAX_DURATION:
        if not temp_video_files:
            break

        video = random.choice(temp_video_files)
        if len(selected_videos) == 1 and video == first_video:
            continue

        video_duration = get_video_duration(video)
        if video_duration is None:
            temp_video_files.remove(video)
            continue

        if total_duration + int(video_duration) > MAX_DURATION:
            temp_video_files.remove(video)
            continue

        selected_videos.append(video)
        total_duration += int(video_duration)
        temp_video_files.remove(video)

    if MIN_DURATION <= total_duration <= MAX_DURATION:
        temp_output_name = os.path.join(OUTPUT_FOLDER, "temp_output.mp4")
        mylist_path = os.path.join(TEMP_FOLDER, "mylist.txt")

        # Dọn temp folder
        for f in os.listdir(TEMP_FOLDER):
            file_path = os.path.join(TEMP_FOLDER, f)
            if os.path.isfile(file_path):
                os.remove(file_path)

        copied_paths = []
        for idx, vid in enumerate(selected_videos):
            temp_name = f"v{idx}.mp4"
            temp_path = os.path.join(TEMP_FOLDER, temp_name)
            shutil.copy2(vid, temp_path)
            copied_paths.append(temp_path)

        with open(mylist_path, "w", encoding="utf-8") as f:
            for path in copied_paths:
                abs_path = escape_path(os.path.abspath(path))
                f.write(f"file '{abs_path}'\n")

        try:
            subprocess.run([
                "ffmpeg", "-f", "concat", "-safe", "0", "-i", mylist_path,
                "-c", "copy", temp_output_name
            ], check=True)

            base_name = os.path.splitext(os.path.basename(first_video))[0]
            base_name_clean = base_name.replace("_", " ")
            final_output_path = os.path.join(OUTPUT_FOLDER, f"{base_name_clean}.mp4")
            shutil.move(temp_output_name, final_output_path)

            print(f"✅ Xuất video: {final_output_path} ({total_duration} giây)")

            # Ghi scene file
            scene_file = os.path.join(OUTPUT_FOLDER, f"{base_name_clean}.scenes.txt")
            with open(scene_file, "w", encoding="utf-8") as f:
                scene_time = 0
                for video in selected_videos:
                    duration = get_video_duration(video)
                    if duration is None:
                        continue
                    h, m, s = scene_time // 3600, (scene_time % 3600) // 60, scene_time % 60
                    formatted_time = f"{h:02}:{m:02}:{s:02}"
                    video_title = os.path.basename(video).replace(".mp4", "").replace("_", " ")
                    f.write(f"{formatted_time} - {video_title}\n")
                    scene_time += int(duration)

            used_first_videos.add(first_video)

        except subprocess.CalledProcessError:
            print(f"[❌] Lỗi khi ghép video: {first_video}")

print("🎬 Hoàn thành tất cả video trong khoảng 55–70 phút.")
