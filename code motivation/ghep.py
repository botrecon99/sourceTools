import os
import random
import subprocess
import logging
import shutil

# === SETUP ===
input_videos_dir = 'input_videos'
input_audios_dir = 'input_audios'
music_dir = 'music'
output_dir = 'output'
processed_state_file = 'processed_state.txt'
backup_dir = 'backups'
cleaned_dir = 'cleaned'
used_heads_file = 'used_video_heads.txt'

# === LOGGING ===
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
file_handler = logging.FileHandler('processing.log', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# === CREATE FOLDERS ===
os.makedirs(output_dir, exist_ok=True)
os.makedirs(backup_dir, exist_ok=True)
os.makedirs(cleaned_dir, exist_ok=True)

# === LOAD STATES ===
def load_state_file(file_path):
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin1') as f:
            return set(f.read().splitlines())

processed_files = load_state_file(processed_state_file)
used_video_heads = load_state_file(used_heads_file)

# === UTILS ===
def mark_head_used(video_path):
    with open(used_heads_file, 'a', encoding='utf-8') as f:
        f.write(f"{video_path}\n")
    used_video_heads.add(video_path)

def save_processed(file_path):
    with open(processed_state_file, 'a', encoding='utf-8') as f:
        f.write(f"{file_path}\n")
    print(f"[✓] Đã lưu: {file_path}")

def backup_media_file(input_path):
    try:
        backup_path = os.path.join(backup_dir, os.path.basename(input_path))
        shutil.copy(input_path, backup_path)
        print(f"[✓] Đã sao lưu: {input_path}")
    except Exception as e:
        logging.error(f"Lỗi backup {input_path}: {e}")

def get_cleaned_path(input_path, media_type):
    base = os.path.splitext(os.path.basename(input_path))[0]
    ext = '.mp4' if media_type == 'video' else '.wav'
    return os.path.join(cleaned_dir, f"{base}_clean{ext}")

def clean_media_file(input_path, output_path, media_type):
    if os.path.exists(output_path):
        return
    try:
        if media_type == 'video':
            cmd = [
                'ffmpeg', '-y', '-hwaccel', 'cuda', '-i', input_path,
                '-vf', 'fps=30,scale=1280:720',
                '-c:v', 'h264_nvenc', '-preset', 'p4', '-rc:v', 'vbr_hq', '-b:v', '5M',
                '-pix_fmt', 'yuv420p', '-an', '-fflags', '+genpts', output_path
            ]
        else:
            cmd = [
                'ffmpeg', '-y', '-i', input_path,
                '-ar', '44100', '-ac', '2',
                '-c:a', 'pcm_s16le', output_path
            ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        logging.error(f"Lỗi clean {media_type} {input_path}: {e}")

def get_audio_duration(audio_path):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        logging.error(f"Lỗi lấy độ dài audio {audio_path}: {e}")
        return 0

def select_unique_head(video_files):
    remaining = list(set(video_files) - used_video_heads)
    if not remaining:
        return None
    chosen = random.choice(remaining)
    mark_head_used(chosen)
    return chosen

# === MAIN FUNCTION ===
def create_final_video(podcast_paths, video_heads, beat_tracks, output_path):
    try:
        timestamps = []
        total_duration = 0
        podcast_audio_list = []
        beat_audio_list = []

        for p in podcast_paths:
            clean_audio = get_cleaned_path(p, 'audio')
            clean_media_file(p, clean_audio, 'audio')
            podcast_audio_list.append(clean_audio)
            dur = get_audio_duration(clean_audio)
            start_time = total_duration
            end_time = start_time + dur
            timestamps.append((p, start_time, end_time))
            total_duration += dur

        if total_duration == 0:
            print("[❌] Audio không có nội dung, bỏ qua.")
            return

        with open('podcast_concat.txt', 'w', encoding='utf-8') as f:
            for a in podcast_audio_list:
                f.write(f"file '{os.path.abspath(a)}'\n")
        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'podcast_concat.txt',
            '-c', 'copy', 'podcast_output.wav'
        ], check=True)

        beat_duration = 0
        while beat_duration < total_duration:
            beat = random.choice(beat_tracks)
            clean_beat = get_cleaned_path(beat, 'audio')
            clean_media_file(beat, clean_beat, 'audio')
            beat_audio_list.append(clean_beat)
            beat_duration += get_audio_duration(clean_beat)

        with open('beat_concat.txt', 'w', encoding='utf-8') as f:
            for a in beat_audio_list:
                f.write(f"file '{os.path.abspath(a)}'\n")
        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'beat_concat.txt',
            '-c', 'copy', 'beat_output.wav'
        ], check=True)

        subprocess.run([
            'ffmpeg', '-y',
            '-i', 'podcast_output.wav',
            '-i', 'beat_output.wav',
            '-filter_complex', '[0:a]volume=1.0[a0];[1:a]volume=0.15[a1];[a0][a1]amix=inputs=2:duration=first',
            '-c:a', 'aac', '-b:a', '192k',
            'final_audio.m4a'
        ], check=True)

        selected_videos = []
        total_video_duration = 0
        head_video = select_unique_head(video_heads)
        if not head_video:
            print("[❌] Không còn video head nào!")
            return

        while total_video_duration < total_duration:
            video = head_video if total_video_duration == 0 else random.choice(video_heads)
            clean_video = get_cleaned_path(video, 'video')
            clean_media_file(video, clean_video, 'video')
            selected_videos.append(clean_video)
            total_video_duration += get_audio_duration(clean_video)

        with open('video_concat.txt', 'w', encoding='utf-8') as f:
            for v in selected_videos:
                f.write(f"file '{os.path.abspath(v)}'\n")
        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'video_concat.txt',
            '-c', 'copy', 'temp_video.mp4'
        ], check=True)

        subprocess.run([
            'ffmpeg', '-y', '-i', 'temp_video.mp4', '-t', str(total_duration),
            '-c', 'copy', 'final_video.mp4'
        ], check=True)

        subprocess.run([
            'ffmpeg', '-y',
            '-i', 'final_video.mp4',
            '-i', 'final_audio.m4a',
            '-c:v', 'h264_nvenc', '-preset', 'p4', '-rc:v', 'vbr_hq', '-b:v', '5M',
            '-c:a', 'aac', '-shortest',
            output_path
        ], check=True)

        for f in [
            'podcast_output.wav', 'beat_output.wav', 'final_audio.m4a',
            'temp_video.mp4', 'final_video.mp4',
            'podcast_concat.txt', 'beat_concat.txt', 'video_concat.txt'
        ]:
            if os.path.exists(f):
                os.remove(f)

        print(f"[🎯] Done: {output_path}")

        for p in podcast_paths:
            save_processed(p)

    except Exception as e:
        logging.error(f"Lỗi tạo video {output_path}: {e}")

# === PROCESS ===
def process_all():
    video_files = [os.path.join(input_videos_dir, f)
                   for f in os.listdir(input_videos_dir) if f.endswith('.mp4')]
    audio_files = [os.path.join(input_audios_dir, f)
                   for f in os.listdir(input_audios_dir) if f.endswith(('.mp3', '.wav'))]
    beat_tracks = [os.path.join(music_dir, f)
                   for f in os.listdir(music_dir) if f.endswith(('.mp3', '.wav'))]

    if not video_files or not audio_files or not beat_tracks:
        print("[❌] Thiếu file input (video/audio/beat). Kiểm tra lại.")
        return

    audio_durations = {a: get_audio_duration(a) for a in audio_files}
    long_audio_files = [(a, d) for a, d in audio_durations.items() if d >= 60*60]
    short_audio_files = [(a, d) for a, d in audio_durations.items() if d < 60*60]

    for a, dur in long_audio_files:
        if a in processed_files:
            continue
        backup_media_file(a)
        base_name = os.path.splitext(os.path.basename(a))[0]
        output_path = os.path.join(output_dir, f"{base_name}.mp4")
        create_final_video([a], video_files, beat_tracks, output_path)

    short_audio_files.sort(key=lambda x: x[1], reverse=True)
    used_in_batch = set()
    i = 0
    while i < len(short_audio_files):
        batch = []
        total_duration = 0
        while i < len(short_audio_files) and total_duration < 60*60:
            a, dur = short_audio_files[i]
            if a in processed_files:
                i += 1
                continue
            batch.append((a, dur))
            used_in_batch.add(a)
            total_duration += dur
            i += 1

        if total_duration < 60*60:
            for a, dur in audio_durations.items():
                if a not in used_in_batch and a not in processed_files:
                    batch.append((a, dur))
                    used_in_batch.add(a)
                    total_duration += dur
                    if total_duration >= 60*60:
                        break

        if total_duration > 90*60:
            batch.sort(key=lambda x: x[1])
            for idx in range(len(batch)):
                test_batch = batch[:idx] + batch[idx+1:]
                test_duration = sum(d for _, d in test_batch)
                if 60*60 <= test_duration <= 90*60:
                    batch = test_batch
                    total_duration = test_duration
                    break

        if batch:
            first_audio_name = os.path.splitext(os.path.basename(batch[0][0]))[0]
            output_path = os.path.join(output_dir, f"{first_audio_name}.mp4")
            backup_media_file(batch[0][0])
            create_final_video([a for a, _ in batch], video_files, beat_tracks, output_path)

# === ENTRY POINT ===
if __name__ == '__main__':
    process_all()
