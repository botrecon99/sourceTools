import os
import re
import json
import subprocess
import assemblyai as aai
from pydub import AudioSegment
from pydub.generators import Sine
from moviepy.editor import VideoFileClip, AudioFileClip

# === CONFIG ===
INPUT_FOLDER = "videos_input"
OUTPUT_FOLDER = "videos_output"
TRANSCRIPT_FOLDER = "transcripts"
TEMP_AUDIO_FOLDER = "temp_audio"
ASSEMBLYAI_API_KEY = "99ea9525425c476c9259e7164bccb2f0"  # Thay bằng API key của bạn

# === TẠO THƯ MỤC NẾU CHƯA CÓ ===
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)
os.makedirs(TEMP_AUDIO_FOLDER, exist_ok=True)

# === TỪ NGỮ CẦN BEEP ===
severe_words = {
    "fuck", "fucking", "motherfucker", "cunt", "nigger", "nigga",
    "retard", "retarded", "retards", "little", "jerk", "jerkoff", "jerk-off",
    "came", "cum", "suck", "dick", "suckdick", "cock", "pussy", "balls", "titties", "boobs"
}
risky_words = {
    "bitch", "asshole", "shit", "bullshit", "damn", "goddamn", "crap",
    "whore", "slut", "prick", "bang", "grind", "moan", "lick", "comeon", "ride", "rideit"
}
bad_words = severe_words | risky_words
beep = Sine(1000).to_audio_segment(duration=500).apply_gain(-10)

# === TẠO TRANSCRIPT TỪ ASSEMBLYAI ===
def generate_transcript(input_file, json_path, srt_path, api_key):
    print("🧠 Đang tạo transcript với AssemblyAI...")
    aai.settings.api_key = api_key
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(input_file)

    # Ghi file SRT
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(transcript.export_subtitles_srt())

    # Ghi file JSON từ từng từ
    segments = []
    for word in transcript.words:
        if word.text.strip():
            segments.append({
                "start": word.start,
                "end": word.end,
                "text": word.text
            })
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)

    print("✅ Transcript đã lưu.")
    return segments

# === ÁP DỤNG BEEP VÀ XUẤT AUDIO MỚI ===
def censor_audio(input_audio_path, segments, output_audio_path):
    audio = AudioSegment.from_file(input_audio_path)
    new_audio = AudioSegment.empty()
    last_end = 0

    for seg in segments:
        start_ms = int(seg["start"])
        end_ms = int(seg["end"])
        word = re.sub(r"[^\w]", "", seg["text"].lower())  # normalize

        # Thêm phần trước từ hiện tại
        if start_ms > last_end:
            new_audio += audio[last_end:start_ms]

        # Bíp nếu là từ nhạy cảm
        if word in bad_words:
            dur = end_ms - start_ms
            new_audio += beep[:dur]
        else:
            new_audio += audio[start_ms:end_ms]

        last_end = end_ms

    # Thêm phần còn lại
    if last_end < len(audio):
        new_audio += audio[last_end:]

    new_audio.export(output_audio_path, format="wav")

# === QUÉT VIDEO TRONG THƯ MỤC ===
video_files = [
    f for f in os.listdir(INPUT_FOLDER)
    if f.lower().endswith((".mp4", ".mov", ".mkv"))
]

for video_file in video_files:
    base = os.path.splitext(video_file)[0]
    input_video = os.path.join(INPUT_FOLDER, video_file)
    input_audio = os.path.join(TEMP_AUDIO_FOLDER, base + ".wav")
    transcript_json = os.path.join(TRANSCRIPT_FOLDER, f"transcript_{base}.json")
    transcript_srt = os.path.join(TEMP_AUDIO_FOLDER, f"{base}.srt")
    censored_audio = os.path.join(TEMP_AUDIO_FOLDER, base + "_censored.wav")
    output_video = os.path.join(OUTPUT_FOLDER, f"{base}_censored.mp4")

    print(f"\n🎬 Đang xử lý: {video_file}")

    # 1. Tách audio từ video
    subprocess.run([
        "ffmpeg", "-y", "-i", input_video,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        input_audio
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 2. Tạo transcript nếu chưa có
    if os.path.exists(transcript_json):
        with open(transcript_json, "r", encoding="utf-8") as f:
            segments = json.load(f)["segments"]
    else:
        segments = generate_transcript(
            input_audio, transcript_json, transcript_srt, ASSEMBLYAI_API_KEY
        )

    # 3. Áp dụng beep vào audio
    censor_audio(input_audio, segments, censored_audio)

    # 4. Ghép lại video với audio đã beep
    video = VideoFileClip(input_video)
    censored_audio_clip = AudioFileClip(censored_audio)
    final_video = video.set_audio(censored_audio_clip)
    final_video.write_videofile(
        output_video,
        codec="libx264",  # hoặc "h264_nvenc" nếu dùng GPU
        audio_codec="aac",
        temp_audiofile=os.path.join(TEMP_AUDIO_FOLDER, f"{base}_temp_audio.m4a"),
        remove_temp=True,
        threads=8,
        preset="fast"
    )

    print(f"✅ Đã lưu video: {output_video}")

print("\n🏁 Hoàn tất toàn bộ.")
