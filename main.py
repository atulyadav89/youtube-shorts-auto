import json
import feedparser
import subprocess

with open("config.json") as f:
    config = json.load(f)

with open("creator_status.json") as f:
    status = json.load(f)

def check_latest_video(channel_id):
    feed = feedparser.parse(
        f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    )
    return feed.entries[0].link

for creator in config["channels"]:
    name = creator["name"]

    if status[name] != "active":
        continue

    video_url = check_latest_video(creator["channel_id"])

    subprocess.run(["yt-dlp", "-f", "mp4", "-o", "video.mp4", video_url])
    subprocess.run(["ffmpeg", "-i", "video.mp4", "-ss", "00:00:05", "-t", "30", "short.mp4"])

    print(f"READY SHORT FOR {name}")
