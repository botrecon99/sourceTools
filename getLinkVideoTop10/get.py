import requests
import re
import time
import os

API_KEY = "AIzaSyAOscjpHbOvdIPHiNVz7sHiJc_SWcdm1O0"
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"

def read_channel_urls(filename="input.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("⚠ Không tìm thấy file input.txt")
        return []

def get_channel_id(channel_url):
    username = channel_url.split("@")[-1].replace("/videos", "")
    url = f"{YOUTUBE_API_URL}/channels?part=id,snippet&forHandle=@{username}&key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "items" in data and len(data["items"]) > 0:
        channel_id = data["items"][0]["id"]
        channel_title = data["items"][0]["snippet"]["title"]
        return channel_id, channel_title
    print(f"❌ Không tìm thấy Channel ID cho {channel_url}")
    return None, None

def convert_duration(duration_str):
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return 0
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    return hours * 3600 + minutes * 60 + seconds

def get_all_videos_from_uploads(channel_id):
    uploads_playlist_id = "UU" + channel_id[2:]
    video_ids = []
    next_page_token = None
    print(f"📥 Đang quét video từ uploads playlist: {uploads_playlist_id}")

    while True:
        url = (
            f"{YOUTUBE_API_URL}/playlistItems?part=contentDetails"
            f"&playlistId={uploads_playlist_id}&maxResults=50&key={API_KEY}"
        )
        if next_page_token:
            url += f"&pageToken={next_page_token}"

        response = requests.get(url)
        data = response.json()

        if "items" not in data:
            print("❌ Lỗi khi gọi playlistItems:", data)
            break

        for item in data["items"]:
            video_id = item["contentDetails"]["videoId"]
            video_ids.append(video_id)

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break
        time.sleep(0.1)

    return video_ids

def get_video_details(video_ids):
    video_data = []

    for i in range(0, len(video_ids), 50):
        batch_ids = ",".join(video_ids[i:i+50])
        url = f"{YOUTUBE_API_URL}/videos?part=snippet,contentDetails,statistics&id={batch_ids}&key={API_KEY}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"❌ Lỗi khi gọi videos API: {response.status_code}, {response.text}")
            time.sleep(1)
            continue

        data = response.json()

        if "items" not in data:
            continue

        for item in data["items"]:
            if "snippet" not in item or "title" not in item["snippet"]:
                continue

            video_id = item["id"]
            title = item["snippet"]["title"]
            duration = convert_duration(item["contentDetails"]["duration"])
            views = int(item["statistics"].get("viewCount", 0))
            link = f"https://www.youtube.com/watch?v={video_id}"

            video_data.append((title, views, duration, link))

        time.sleep(0.1)

    return video_data

def load_processed_ids(filename="processed_videos.txt"):
    if not os.path.exists(filename):
        return set()
    with open(filename, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_ids(video_ids, filename="processed_videos.txt"):
    with open(filename, "a", encoding="utf-8") as f:
        for vid in video_ids:
            f.write(f"{vid}\n")

def process_channel(channel_url, processed_ids):
    channel_id, channel_name = get_channel_id(channel_url)
    if not channel_id:
        return []

    all_video_ids = get_all_videos_from_uploads(channel_id)
    all_video_data = get_video_details(all_video_ids)

    # Bỏ video Shorts (dưới 60 giây) và đã xử lý trước đó
    filtered = [
        v for v in all_video_data
        if v[2] >= 60 and v[3].split('=')[-1] not in processed_ids
    ]

    # Lấy top 10 nhiều lượt xem nhất
    top_10 = sorted(filtered, key=lambda x: x[1], reverse=True)[:10]

    # Lưu video_id đã xử lý
    new_ids = [v[3].split('=')[-1] for v in top_10]
    save_processed_ids(new_ids)
    processed_ids.update(new_ids)

    return [(channel_name, *v) for v in top_10]

def main():
    processed_ids = load_processed_ids()
    channel_urls = read_channel_urls()
    all_top_10 = []

    for channel_url in channel_urls:
        print(f"\n📡 Đang xử lý kênh: {channel_url}")
        top_10 = process_channel(channel_url, processed_ids)
        all_top_10.extend(top_10)

    with open("output_top10.txt", "a", encoding="utf-8") as f:
        for channel, title, views, duration, link in all_top_10:
            minutes = round(duration / 60, 1)
            f.write(f"{channel} - {link} - {minutes} phút - {views} lượt xem\n")

    print("\n✅ Đã cập nhật output_top10.txt và lưu lịch sử vào processed_videos.txt")

if __name__ == "__main__":
    main()
