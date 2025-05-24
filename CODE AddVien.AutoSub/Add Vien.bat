for %%t in ("input\*.*") DO ffmpeg -y -i "%%t" -i "Vien.png" -filter_complex "[0:v]scale=1920x1080[v0];[v0][1:v] overlay=0:0[v1]" -map [v1] -map 0:a "videos_input\%%~nt.mp4"
pause