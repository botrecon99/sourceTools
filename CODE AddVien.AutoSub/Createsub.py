import os
import assemblyai as aai
import subprocess
import shutil
import traceback
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Thiết lập API key từ biến môi trường
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
if not aai.settings.api_key:
    raise ValueError("⚠️ ASSEMBLYAI_API_KEY không được tìm thấy trong file .env")

transcriber = aai.Transcriber()

# Đường dẫn thư mục và font
input_folder = "videos_input"
output_folder = "videos_output"
font_path = "Arial\\ARIALBD.TTF"  # Đảm bảo đây là đường dẫn tới font Arial Bold
font_dir = os.path.dirname(font_path)  # Đường dẫn thư mục chứa font

# File tạm
temp_video_path = f"{input_folder}/__running_video.mp4"
temp_audio_path = f"{input_folder}/__running_audio.mp3"
temp_srt_path = f"{input_folder}/__running_subs.srt"

# Tạo thư mục output nếu chưa có
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.mp4', '.mov', '.mkv', '.avi')):
        input_path = os.path.join(input_folder, filename)
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_folder, filename)
        srt_output_path = os.path.join(input_folder, f"{base_name}.srt")

        if os.path.exists(output_path):
            print(f"⏭️ Bỏ qua (đã xử lý): {filename}")
            continue

        try:
            print(f"\n🔄 Đang xử lý: {filename}")

            # Sao chép video vào file tạm để tránh lỗi ký tự đặc biệt
            shutil.copy(input_path, temp_video_path)

            # Trích xuất âm thanh
            subprocess.run(
                f'ffmpeg -y -i "{temp_video_path}" -q:a 0 -map a "{temp_audio_path}"',
                shell=True,
                check=True
            )

            # Gửi tới AssemblyAI để tạo phụ đề
            transcript = transcriber.transcribe(temp_audio_path)

            # Lưu file phụ đề
            with open(temp_srt_path, "w", encoding="utf-8") as f:
                f.write(transcript.export_subtitles_srt())

            shutil.copy(temp_srt_path, srt_output_path)

            # Tạo bộ lọc phụ đề với nền cho chữ (chỉ nền cho chữ, không làm nền toàn bộ video)
            subtitle_style = (
                f"subtitles='{temp_srt_path}':"
                f"fontsdir='{font_dir}':"
                f"force_style='FontName=Arial-Bold,FontSize=35,"  # Sử dụng font Arial Bold, chữ lớn
                f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,BorderStyle=1,Shadow=0,"  # Chữ trắng, viền đen, không bóng
                f"BackColour=&H80000000,BackOpacity=0.8,Box=1'"  # Chỉ thêm nền cho chữ, không phải toàn bộ video
            )

            # Gắn phụ đề vào video
            subprocess.run(
                f'ffmpeg -y -i "{temp_video_path}" -vf "{subtitle_style}" -c:v libx264 -c:a aac "{output_path}"',
                shell=True,
                check=True
            )

            print(f"✅ Hoàn tất: {filename}")

        except Exception as e:
            traceback.print_exc()
            print(f"❌ Lỗi với video {filename}: {e}")

        finally:
            # Xoá file tạm
            for path in [temp_video_path, temp_audio_path, temp_srt_path]:
                if os.path.exists(path):
                    os.remove(path)

print("🎉 Hoàn tất toàn bộ quá trình!")
