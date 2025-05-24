import os
import subprocess
import pandas as pd
from moviepy.editor import VideoFileClip

# Thư mục nguồn
content_folder = 'content'
reup_folder = 'reup'
output_folder = 'output'

# Tạo thư mục output nếu chưa có
os.makedirs(output_folder, exist_ok=True)

# Lọc video
valid_video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv']
content_files = sorted([f for f in os.listdir(content_folder) if any(f.lower().endswith(ext) for ext in valid_video_exts)])
reup_files = sorted([f for f in os.listdir(reup_folder) if any(f.lower().endswith(ext) for ext in valid_video_exts)])

print(f"🧾 Số video content: {len(content_files)}")
print(f"🧾 Số video reup: {len(reup_files)}")

if len(content_files) != len(reup_files):
    print("❌ Số lượng file không khớp giữa 'content' và 'reup'.")
    exit()

def has_audio(video_path):
    result = subprocess.run(
        ['ffprobe', '-i', video_path, '-show_streams', '-select_streams', 'a', '-loglevel', 'error'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return "codec_type=audio" in result.stdout

video_info = []

for content_video, reup_video in zip(content_files, reup_files):
    content_path = os.path.join(content_folder, content_video)
    reup_path = os.path.join(reup_folder, reup_video)
    output_path = os.path.join(output_folder, reup_video)

    # Lấy thời lượng
    content_clip = VideoFileClip(content_path)
    content_duration = content_clip.duration
    content_clip.close()

    reup_clip = VideoFileClip(reup_path)
    reup_duration = reup_clip.duration
    reup_clip.close()

    # Kiểm tra audio
    has_audio_content = has_audio(content_path)
    has_audio_reup = has_audio(reup_path)

    filter_complex = []
    input_args = ['ffmpeg', '-y', '-i', content_path, '-i', reup_path]
    audio_inputs = []

    filter_complex.append('[0:v]scale=1280:720,setdar=16/9[v0]')
    filter_complex.append('[1:v]scale=1280:720,setdar=16/9[v1]')

    if not has_audio_content:
        input_args += ['-f', 'lavfi', '-t', str(content_duration), '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100']
        audio_inputs.append('2:a')
    else:
        audio_inputs.append('0:a')

    if not has_audio_reup:
        input_args += ['-f', 'lavfi', '-t', str(reup_duration), '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100']
        audio_inputs.append(str(len(input_args) // 2) + ':a')  # vị trí của input kế tiếp
    else:
        audio_inputs.append('1:a')

    # concat
    filter_complex.append(f'[v0][{audio_inputs[0]}][v1][{audio_inputs[1]}]concat=n=2:v=1:a=1[v][a]')

    ffmpeg_cmd = input_args + [
        '-filter_complex', ';'.join(filter_complex),
        '-map', '[v]', '-map', '[a]',
        '-crf', '25', '-preset', 'ultrafast', '-vsync', 'vfr',
        output_path
    ]

    print(f"🚀 Ghép: {content_video} + {reup_video}")
    subprocess.run(ffmpeg_cmd)

    # Ghi log
    video_info.append({
        'Tên Video Content': content_video,
        'Thời lượng Content (phút:giây)': f"{int(content_duration // 60):02d}:{int(content_duration % 60):02d}",
        'Tên Video Reup': reup_video,
        'Thời lượng Reup (phút:giây)': f"{int(reup_duration // 60):02d}:{int(reup_duration % 60):02d}"
    })

# Xuất Excel
df = pd.DataFrame(video_info)
df.to_excel('video_info.xlsx', index=False)
print("✅ Đã hoàn thành việc ghép video và lưu thông tin vào video_info.xlsx.")
