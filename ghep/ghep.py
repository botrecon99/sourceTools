import os
import glob
import random
import subprocess
import shutil
from config import INPUT_FOLDER, OUTPUT_FOLDER, LOG_FOLDER

MIN_DURATION = 3300   # 55 phút
MAX_DURATION = 4200   # 70 phút
TEMP_FOLDER = "temp_ffmpeg_safe"

os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

video_files = glob.glob(os.path.join(INPUT_FOLDER, "*.mp4"))
random.shuffle(video_files)

if not video_files:
    print("❌ Không có video nào trong thư mục input_videos.")
    exit()

used_first_videos = set()
part_counter = 1

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
        temp_output_name = os.path.join(OUTPUT_FOLDER, f"temp_output_{part_counter}.mp4")
        mylist_path = os.path.join(TEMP_FOLDER, "mylist.txt")

        # Dọn temp folder
        for f in os.listdir(TEMP_FOLDER):
            file_path = os.path.join(TEMP_FOLDER, f)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Copy video vào thư mục tạm
        copied_paths = []
        for idx, vid in enumerate(selected_videos):
            temp_name = f"v{idx}.mp4"
            temp_path = os.path.join(TEMP_FOLDER, temp_name)
            shutil.copy2(vid, temp_path)
            copied_paths.append(temp_path)

        # Ghi mylist.txt với đường dẫn tuyệt đối
        with open(mylist_path, "w", encoding="utf-8") as f:
            for path in copied_paths:
                abs_path = os.path.abspath(path).replace("\\", "/")
                f.write(f"file '{abs_path}'\n")

        try:
            subprocess.run([
                "ffmpeg", "-f", "concat", "-safe", "0", "-i", mylist_path,
                "-c", "copy", temp_output_name
            ], check=True)

            final_name = f"{os.path.basename(first_video)}_part{part_counter}.mp4"
            final_output_path = os.path.join(OUTPUT_FOLDER, final_name)
            shutil.move(temp_output_name, final_output_path)

            print(f"✅ Ghép xong: {final_output_path} ({total_duration} giây)")

            scene_file = os.path.join(OUTPUT_FOLDER, f"{os.path.basename(first_video)}_part{part_counter}_scenes.txt")
            with open(scene_file, "w", encoding="utf-8") as f:
                scene_time = 0
                for video in selected_videos:
                    duration = get_video_duration(video)
                    if duration is None:
                        continue
                    h, m, s = scene_time // 3600, (scene_time % 3600) // 60, scene_time % 60
                    formatted_time = f"{h:02}:{m:02}:{s:02}"
                    video_title = os.path.basename(video).replace(".mp4", "")
                    f.write(f"{formatted_time} - {video_title}\n")
                    scene_time += int(duration)

            used_first_videos.add(first_video)
            part_counter += 1

        except subprocess.CalledProcessError:
            print(f"[❌] Lỗi khi ghép video: {first_video}")

print("🎬 Hoàn thành tất cả video trong khoảng 55–70 phút.")
