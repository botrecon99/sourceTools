import whisper
import subprocess
import os

def extract_audio(video_path, audio_path="temp_audio.wav"):
    """
    Tách audio từ video bằng ffmpeg.
    """
    command = ["ffmpeg", "-i", video_path, "-ac", "1", "-ar", "16000", "-vn", audio_path, "-y"]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_path

def transcribe_audio(audio_path, output_srt="output.srt", output_txt="output.txt"):
    """
    Chạy Whisper để nhận diện phụ đề từ audio và lưu ra file SRT.
    """
    model = whisper.load_model("small")  # Chọn mô hình nhỏ để tăng tốc, có thể thay bằng 'medium' hoặc 'large'
    result = model.transcribe(audio_path)

    # Lưu SRT
    with open(output_srt, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(result["segments"]):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]

            # Chuyển đổi thời gian thành định dạng SRT
            start_srt = f"{int(start // 3600):02}:{int(start % 3600 // 60):02}:{int(start % 60):02},{int(start % 1 * 1000):03}"
            end_srt = f"{int(end // 3600):02}:{int(end % 3600 // 60):02}:{int(end % 60):02},{int(end % 1 * 1000):03}"

            srt_file.write(f"{i+1}\n{start_srt} --> {end_srt}\n{text}\n\n")

    # Lưu TXT (không có timestamp)
    with open(output_txt, "w", encoding="utf-8") as txt_file:
        txt_file.write(result["text"])

    print(f"✅ Phụ đề đã lưu: {output_srt}, {output_txt}")

def extract_and_transcribe(video_path):
    """
    Quá trình đầy đủ: Tách audio, nhận diện phụ đề, lưu file SRT & TXT.
    """
    audio_path = extract_audio(video_path)
    transcribe_audio(audio_path)

# 🔥 Chạy tool
video_path = "input.mp4"  # Đổi thành file video của bạn
extract_and_transcribe(video_path)
