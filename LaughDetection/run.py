import os
import re
import subprocess
import numpy as np
from datetime import timedelta
from scipy.io import wavfile
import tensorflow as tf
import keras
from audioset import vggish_embeddings

# === CONFIG ===
INPUT_FOLDER = 'input_videos'
OUTPUT_FOLDER = 'output_videos'
KERAS_MODEL_PATH = 'Models/LSTM_SingleLayer_100Epochs.h5'
THRESHOLD = 0.7
THRESHOLD_PEAK = 0.9
SAMPLE_LEN = 3.0
RATE = 16000
CHUNK = int(SAMPLE_LEN * RATE)

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === UTILITY FUNCTIONS ===
def sec_to_time(secs):
    td = timedelta(seconds=int(secs))
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes}:{seconds:02}"

def score_to_title(score):
    if score >= 0.95:
        return "Audience loses it!"
    elif score >= 0.9:
        return "Epic Laugh!"
    elif score >= 0.85:
        return "Great Moment"
    else:
        return "Mildly Funny"

def sanitize_filename(name):
    return re.sub(r'[^\w\-_\. ]', '_', name)

# === MODEL LOADING ===
print("🚀 Loading model to GPU...")
model = keras.models.load_model(KERAS_MODEL_PATH)
audio_embed = vggish_embeddings.VGGishEmbedder()

# === PROCESS EACH VIDEO ===
for filename in os.listdir(INPUT_FOLDER):
    if not filename.lower().endswith('.mp4'):
        continue

    input_path = os.path.join(INPUT_FOLDER, filename)
    name_base = os.path.splitext(filename)[0]
    sanitized_name = sanitize_filename(name_base)
    clips_folder = os.path.join(OUTPUT_FOLDER, f'clips_{sanitized_name}')
    output_video = os.path.join(OUTPUT_FOLDER, f'{sanitized_name}_laughs.mp4')
    concat_list = os.path.join(clips_folder, 'segments_to_concat.txt')
    laugh_csv = os.path.join(clips_folder, 'laugh_segments.csv')
    temp_wav = os.path.join(clips_folder, 'temp_audio.wav')

    os.makedirs(clips_folder, exist_ok=True)

    # === AUDIO EXTRACTION ===
    print(f"\n🎧 Extracting audio: {filename}")
    subprocess.run([
        'ffmpeg', '-y', '-hwaccel', 'cuda', '-i', input_path,
        '-ac', '1', '-ar', str(RATE), '-vn',
        '-c:a', 'pcm_s16le', temp_wav
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    rate, data = wavfile.read(temp_wav)
    if data.ndim == 2:
        data = data.mean(axis=1).astype(np.int16)

    assert rate == RATE, f"Sample rate mismatch: expected {RATE}, got {rate}"

    # === LAUGHTER DETECTION ===
    num_chunks = len(data) // CHUNK
    print("🔍 Running laughter detection...")
    results = []
    for i in range(num_chunks):
        chunk = data[i * CHUNK:(i + 1) * CHUNK]
        embeddings = audio_embed.convert_waveform_to_embedding(chunk, RATE)
        score = float(model.predict(np.expand_dims(embeddings, axis=0), verbose=0)[0, 0])
        start = round(i * SAMPLE_LEN, 2)
        end = round(start + SAMPLE_LEN, 2)
        results.append((start, end, score))

    os.remove(temp_wav)

    laugh_segments = [r for r in results if r[2] >= THRESHOLD]
    if not laugh_segments:
        print("⚠️ No laugh detected above threshold.")
        continue

    # === MERGE LAUGH SEGMENTS ===
    merged_segments, buffer = [], []
    for seg in laugh_segments:
        if not buffer or seg[0] - buffer[-1][1] <= 10:
            buffer.append(seg)
        else:
            merged_segments.append((buffer[0][0], buffer[-1][1], max([s[2] for s in buffer])))
            buffer = [seg]
    if buffer:
        merged_segments.append((buffer[0][0], buffer[-1][1], max([s[2] for s in buffer])))

    # === SAVE CSV ===
    with open(laugh_csv, 'w', encoding='utf-8') as f:
        f.write("start,end,duration,score,title\n")
        for idx, (start, end, score) in enumerate(merged_segments):
            mid = (start + end) / 2
            clip_start = max(0, mid - 20)
            clip_end = mid + 5

            # Look ahead 30s for high laugh peak
            for s, e, sc in results:
                if clip_end <= s <= clip_end + 30 and sc >= THRESHOLD_PEAK:
                    clip_end = e
                    break

            duration = clip_end - clip_start
            title = score_to_title(score)
            f.write(f"{sec_to_time(clip_start)},{sec_to_time(clip_end)},{round(duration,1)},{round(score,3)},\"{title}\"\n")

    # === CUT VIDEO CLIPS ===
    print("✂️ Cutting and saving segments...")
    with open(concat_list, 'w', encoding='utf-8') as f:
        for idx, (start, end, score) in enumerate(merged_segments):
            mid = (start + end) / 2
            clip_start = max(0, mid - 20)
            clip_end = mid + 5

            # Look ahead 30s for high laugh peak
            for s, e, sc in results:
                if clip_end <= s <= clip_end + 30 and sc >= THRESHOLD_PEAK:
                    clip_end = e
                    break

            out_clip = os.path.join(clips_folder, f"clip_{idx+1:03d}.mp4")
            subprocess.run([
                'ffmpeg', '-y', '-hwaccel', 'cuda', '-ss', str(clip_start), '-to', str(clip_end), '-i', input_path,
                '-c:v', 'h264_nvenc', '-preset', 'p1', '-b:v', '3M',
                '-c:a', 'aac', '-b:a', '128k',
                '-movflags', '+faststart', '-avoid_negative_ts', 'make_zero',
                out_clip
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            abs_path = os.path.abspath(out_clip).replace("\\", "/")
            if os.path.exists(out_clip) and os.path.getsize(out_clip) > 0:
                f.write(f"file '{abs_path}'\n")
            else:
                print(f"⚠️ Skipping faulty clip: {out_clip}")

    # === CONCATENATE CLIPS ===
    print("📦 Concatenating final video...")
    result = subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', concat_list, '-c:v', 'h264_nvenc', '-preset', 'p1', '-c:a', 'aac',
        output_video
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0 and os.path.exists(output_video) and os.path.getsize(output_video) > 0:
        print(f"✅ Done: {output_video}")
    else:
        print(f"❌ Failed to create: {output_video}")
        print("FFmpeg error:")
        print(result.stderr.decode())
