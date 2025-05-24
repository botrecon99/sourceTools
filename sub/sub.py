import os
import subprocess
import assemblyai as aai
import re

# === 1. CẤU HÌNH ===
VIDEO_FILE = "input/videos/video.mp4"     # Đường dẫn video gốc
API_KEY = "99ea9525425c476c9259e7164bccb2f0"  # AssemblyAI API Key

SRT_FILE = "output/subtitles.srt"
ASS_FILE = "output/subtitles.ass"
FINAL_VIDEO = "output/final_horizontal.mp4"

# Tạo thư mục nếu chưa có
os.makedirs("output", exist_ok=True)

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    centiseconds = int((seconds % 1) * 100)
    seconds = int(seconds)
    return f"{hours:01d}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

def split_into_segments(words, max_words=10):
    """Chia transcript thành các đoạn ngắn (1-2 dòng, tối đa max_words/từng dấu chấm)"""
    segments = []
    current = []
    for word in words:
        current.append(word)
        if (len(current) >= max_words or re.search(r'[.!?]', word.text)):
            segments.append(current)
            current = []
    if current:
        segments.append(current)
    return segments

# === TẠO PHỤ ĐỀ KARAOKE BẰNG ASSEMBLYAI ===
def generate_karaoke_subtitles(input_file, srt_path, ass_path, api_key):
    print("🧠 Đang tạo phụ đề karaoke bằng AssemblyAI...")
    aai.settings.api_key = api_key
    transcriber = aai.Transcriber()
    print("🎯 Đang transcribe từng từ...")
    transcript = transcriber.transcribe(input_file)
    words = transcript.words
    segments = split_into_segments(words, max_words=10)
    # Tạo file SRT (từng đoạn)
    with open(srt_path, "w", encoding="utf-8") as f:
        idx = 1
        for seg in segments:
            start_ms = seg[0].start
            end_ms = seg[-1].end
            text = " ".join(w.text.upper() for w in seg)
            start_time = format_time(start_ms / 1000.0).replace(".", ",")
            end_time = format_time(end_ms / 1000.0).replace(".", ",")
            f.write(f"{idx}\n{start_time} --> {end_time}\n{text}\n\n")
            idx += 1
    print(f"✅ Đã lưu phụ đề SRT: {srt_path}")
    # Tạo file ASS karaoke từng đoạn, highlight từng từ
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Bold,100,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,8,0,2,10,10,20,1
Style: Highlight,Arial Bold,100,&H0000FFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,8,0,2,10,10,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        for seg in segments:
            for i, word in enumerate(seg):
                start_time = format_time(word.start / 1000.0)
                end_time = format_time(word.end / 1000.0)
                # Tạo list các từ cho đoạn
                words_list = [w.text for w in seg]
                # Chèn tag màu vào đúng từ đang nói
                words_list[i] = "{\\c&H00FFFF&}" + words_list[i] + "{\\r}"
                highlighted_text = "{\\r}" + " ".join(words_list)
                f.write(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{highlighted_text}\n")
    print(f"✅ Đã lưu phụ đề karaoke ASS: {ass_path}")

# === BURN-IN PHỤ ĐỀ VÀO VIDEO NGANG (YouTube) ===
def burn_subtitles_horizontal(input_file, ass_file, output_file):
    print("🔥 Đang burn-in phụ đề karaoke vào video ngang (YouTube)...")
    input_file = input_file.replace("\\", "/")
    ass_file = ass_file.replace("\\", "/")
    output_file = output_file.replace("\\", "/")
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", input_file,
        "-vf", f"ass={ass_file}",
        "-c:v", "h264_nvenc",
        "-c:a", "copy",
        output_file
    ]
    subprocess.run(command)
    print(f"🎉 Video cuối cùng: {output_file}")

# === CHẠY TOÀN BỘ QUY TRÌNH ===
generate_karaoke_subtitles(VIDEO_FILE, SRT_FILE, ASS_FILE, API_KEY)
burn_subtitles_horizontal(VIDEO_FILE, ASS_FILE, FINAL_VIDEO)
