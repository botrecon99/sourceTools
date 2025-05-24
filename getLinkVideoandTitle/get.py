import requests
import re
import time

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
        return channel_id
    print(f"❌ Không tìm thấy Channel ID cho {channel_url}")
    return None

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
        url = f"{YOUTUBE_API_URL}/videos?part=snippet,contentDetails&id={batch_ids}&key={API_KEY}"
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

            title = item["snippet"]["title"]
            duration = convert_duration(item["contentDetails"]["duration"])
            video_id = item["id"]
            link = f"https://www.youtube.com/watch?v={video_id}"

            # Loại Shorts
            if duration < 60 or "short" in title.lower():
                continue

            video_data.append(f"{title} - {link}")

        time.sleep(0.1)

    return video_data

def process_channel(channel_url):
    channel_id = get_channel_id(channel_url)
    if not channel_id:
        return []

    all_video_ids = get_all_videos_from_uploads(channel_id)
    return get_video_details(all_video_ids)

def main():
    channel_urls = read_channel_urls()
    all_titles = []

    for channel_url in channel_urls:
        print(f"\n📡 Đang xử lý kênh: {channel_url}")
        titles = process_channel(channel_url)
        all_titles.extend(titles)

    with open("output_titles.txt", "w", encoding="utf-8") as f:
        f.write(",".join(all_titles))

    print("\n✅ Đã xuất danh sách tiêu đề vào output_titles.txt (phân cách bằng dấu phẩy)")

if __name__ == "__main__":
    main()
