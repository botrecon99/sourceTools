import os
import shutil
import pandas as pd

# Cấu hình
excel_path = 'phan_loai_chu_de_final.xlsx'  # Thay bằng tên file thực tế nếu khác
root_dir = 'moment'    # Thư mục chứa các folder gốc
output_root = 'video_theo_chu_de'  # Nơi lưu các video đã phân loại theo chủ đề

# Đọc file Excel
df = pd.read_excel(excel_path)

# Lặp qua từng dòng
for idx, row in df.iterrows():
    folder = str(row['Folder']).strip()
    video_name = str(row['Video Name']).strip()
    topic = str(row['Chủ đề tổng quát']).strip()

    # Bỏ qua nếu thiếu thông tin
    if not all([folder, video_name, topic]) or topic.lower() == 'nan':
        continue

    # Đường dẫn file gốc
    source_path = os.path.join(root_dir, folder, video_name)
    
    # Đường dẫn thư mục đích
    target_dir = os.path.join(output_root, topic)
    os.makedirs(target_dir, exist_ok=True)

    # Đường dẫn file đích
    target_path = os.path.join(target_dir, video_name)

    # Copy nếu tồn tại
    if os.path.isfile(source_path):
        print(f"✅ Copying: {source_path} → {target_path}")
        shutil.copy2(source_path, target_path)
    else:
        print(f"❌ Not Found: {source_path}")
