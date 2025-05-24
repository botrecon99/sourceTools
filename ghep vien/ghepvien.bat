@echo off
setlocal enabledelayedexpansion

:: Tạo thư mục output nếu chưa có
if not exist "output" mkdir "output"

:: Đường dẫn đến ảnh viền
set "border_image=vien1.png"

:: Duyệt tất cả các file trong thư mục input
for %%t in ("input\*.*") do (
    echo 🔧 Đang xử lý: %%~nt.mp4
    start "" /B cmd /c ffmpeg -y -i "%%t" -i "%border_image%" -filter_complex "[0:v]scale=1280x720[v0];[v0][1:v]overlay=0:0[v1]" -map "[v1]" -map 0:a -c:v libx264 -preset ultrafast -crf 23 -c:a aac -b:a 128k "output\%%~nt.mp4"
)

echo ✅ Đang xử lý tất cả video song song. Vui lòng đợi hoàn tất...
pause
