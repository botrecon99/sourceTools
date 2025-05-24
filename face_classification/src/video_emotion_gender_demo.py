import cv2
import os
import subprocess
import numpy as np
from collections import deque
from keras.models import load_model

from utils.inference import detect_faces, apply_offsets, load_detection_model
from utils.preprocessor import preprocess_input
from utils.datasets import get_labels

# ===== CONFIG =====
input_video_path = "input.mp4"
output_folder = "output_clips"
timestamps_log = os.path.join(output_folder, "timestamps.txt")
merged_output = os.path.join(output_folder, "final_highlight.mp4")
os.makedirs(output_folder, exist_ok=True)

# ===== MODEL =====
detection_model_path = 'trained_models/detection_models/haarcascade_frontalface_default.xml'
emotion_model_path = 'trained_models/fer2013_mini_XCEPTION.119-0.65.hdf5'
emotion_labels = get_labels('fer2013')
emotion_target = ['Happy', 'Surprise']

emotion_classifier = load_model(emotion_model_path, compile=False)
face_detection = load_detection_model(detection_model_path)
emotion_target_size = emotion_classifier.input_shape[1:3]

# ===== VIDEO INFO =====
cap = cv2.VideoCapture(input_video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    raise ValueError("Không đọc được FPS từ video. Kiểm tra lại file input.mp4.")
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = frame_count / fps

# ===== PHÂN TÍCH CẢM XÚC =====
segments = []
emotion_window = deque(maxlen=10)
segment_start = None
segment_emotion = None

frame_idx = 0
while True:
    ret, bgr_image = cap.read()
    if not ret:
        break
    frame_time = frame_idx / fps
    gray_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    faces = detect_faces(face_detection, gray_image)

    dominant_emotion = None
    for face_coordinates in faces:
        x1, x2, y1, y2 = apply_offsets(face_coordinates, (0, 0))
        gray_face = gray_image[y1:y2, x1:x2]
        try:
            gray_face = cv2.resize(gray_face, emotion_target_size)
        except:
            continue

        gray_face = preprocess_input(gray_face, True)
        gray_face = np.expand_dims(gray_face, 0)
        gray_face = np.expand_dims(gray_face, -1)

        emotion_prediction = emotion_classifier.predict(gray_face)[0]
        emotion_label_arg = np.argmax(emotion_prediction)
        emotion_text = emotion_labels[emotion_label_arg]
        emotion_window.append(emotion_text)

    if emotion_window:
        dominant_emotion = max(set(emotion_window), key=emotion_window.count)

    if dominant_emotion in emotion_target:
        if segment_start is None:
            segment_start = frame_time
            segment_emotion = dominant_emotion
    else:
        if segment_start is not None:
            if frame_time - segment_start >= 2:
                segments.append((segment_start, frame_time, segment_emotion))
            segment_start = None
            segment_emotion = None

    frame_idx += 1

cap.release()

# ===== GHI LOG Timestamps =====
with open(timestamps_log, "w", encoding="utf-8") as f:
    for idx, (start, end, emo) in enumerate(segments):
        f.write(f"{idx+1:03}: {emo} from {start:.2f}s to {end:.2f}s\n")

# ===== CẮT VIDEO THEO EMOTION =====
cut_files = []

def cut_segment(start, end, idx):
    output_path = os.path.join(output_folder, f"{idx:03}_highlight.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video_path,
        "-ss", str(start),
        "-to", str(end),
        "-c:v", "copy", "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cut_files.append(output_path)

for idx, (start, end, _) in enumerate(segments):
    cut_segment(start, end, idx)

# ===== GHÉP THÀNH 1 VIDEO DUY NHẤT =====
concat_list_path = os.path.join(output_folder, "concat_list.txt")
with open(concat_list_path, "w", encoding="utf-8") as f:
    for path in cut_files:
        f.write(f"file '{os.path.abspath(path)}'\n")

if cut_files:
    cmd_merge = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy", merged_output
    ]
    subprocess.run(cmd_merge, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✅ Đã tạo video tổng hợp: {merged_output}")
else:
    print("Không tìm thấy đoạn cảm xúc nào phù hợp để cắt.")

print(f"📄 Danh sách đoạn highlight: {timestamps_log}")
