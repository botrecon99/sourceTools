# config.py - Chứa cấu hình chính
INPUT_FOLDER = "input_videos"  # Thư mục chứa video đầu vào
OUTPUT_FOLDER = "output_videos"  # Thư mục chứa video sau khi ghép
LOG_FOLDER = "logs"  # Thư mục chứa file log

MAX_DURATION = 4200  # Thời lượng tối đa của mỗi video ghép (giây)
TIME_FILE = f"{LOG_FOLDER}/time.txt"
VIDEO_LIST_FILE = f"{LOG_FOLDER}/video_list.txt"
USED_FIRST_VIDEOS_FILE = f"{LOG_FOLDER}/used_first_videos.txt"