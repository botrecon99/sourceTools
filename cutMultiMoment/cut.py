import os
import re
import subprocess
from moviepy.editor import VideoFileClip

input_folder = 'input_videos'
output_folder = 'moment'

def normalize_time(t):
    t = t.strip()
    if ':' in t:
        return t.zfill(5) if len(t.split(":")) == 2 else t
    if not t.isdigit():
        return None
    if len(t) == 4:  # MMSS
        return f"{t[:2]}:{t[2:]}"
    elif len(t) == 6:  # HHMMSS
        return f"{t[:2]}:{t[2:4]}:{t[4:]}"
    elif len(t) == 3:  # MSS
        return f"00:{t[0]}:{t[1:]}"
    elif len(t) == 2:  # SS
        return f"00:{t}"
    elif len(t) == 5:  # HMMSS
        return f"0{t[0]}:{t[1:3]}:{t[3:]}"
    return None

def timestamp_to_seconds(ts):
    parts = list(map(int, ts.strip().split(":")))
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0

def get_video_duration(path):
    try:
        clip = VideoFileClip(path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        print(f"❌ Lỗi đọc video: {e}")
        return 0

def cut_clip_ffmpeg(video_path, start, end, output_path):
    command = [
        'ffmpeg', '-y', '-i', video_path,
        '-ss', start, '-to', end,
        '-c', 'copy', output_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def extract_timestamps_from_block(text):
    pattern = r"\((\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]\s*(\d{1,2}:\d{2}(?::\d{2})?)\)"
    return re.findall(pattern, text)

def process_videos():
    videos = [f for f in os.listdir(input_folder) if f.lower().endswith(('.mp4', '.mov', '.mkv', '.avi'))]
    if not videos:
        print("⚠️ Không tìm thấy video nào trong thư mục input_videos/")
        return

    for video_file in videos:
        video_path = os.path.join(input_folder, video_file)
        video_name = os.path.splitext(video_file)[0]
        output_subfolder = os.path.join(output_folder, video_name)
        os.makedirs(output_subfolder, exist_ok=True)

        print(f"\n🎬 Đang xử lý video: {video_file}")
        duration = get_video_duration(video_path)
        print(f"⏱ Thời lượng: {int(duration)} giây")

        print("📋 Dán toàn bộ đoạn timestamp (dạng (00:01–03:02)) rồi ENTER 2 lần để bắt đầu:")
        lines = []
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line)
        raw_text = '\n'.join(lines)

        timestamps = extract_timestamps_from_block(raw_text)
        if not timestamps:
            print("❌ Không phát hiện timestamp hợp lệ.")
            continue

        count = 1
        for start_raw, end_raw in timestamps:
            try:
                start_str = normalize_time(start_raw)
                end_str = normalize_time(end_raw)
                if not start_str or not end_str:
                    raise ValueError("⛔ Định dạng thời gian không hợp lệ.")

                start_sec = timestamp_to_seconds(start_str)
                end_sec = timestamp_to_seconds(end_str)

                if start_sec >= end_sec:
                    print(f"⚠️ Bỏ qua: {start_str} >= {end_str}")
                    continue
                if end_sec > duration:
                    print(f"⚠️ Bỏ qua vì quá thời lượng: {end_str} > {int(duration)}s")
                    continue

                output_path = os.path.join(output_subfolder, f"clip_{count:02d}.mp4")
                print(f"✂️ Cắt từ {start_str} đến {end_str} → {output_path}")
                cut_clip_ffmpeg(video_path, start_str, end_str, output_path)
                count += 1
            except Exception as e:
                print(f"❌ Lỗi xử lý đoạn ({start_raw}–{end_raw}): {e}")

        try:
            os.remove(video_path)
            print(f"🗑️ Đã xóa video gốc: {video_file}")
        except Exception as e:
            print(f"⚠️ Không thể xóa file: {e}")

while True:
    process_videos()
    again = input("\n❓ Xử lý video khác? (Y để tiếp tục, E để thoát): ").strip().upper()
    if again == 'E':
        print("👋 Kết thúc chương trình.")
        break
