import os
import json
import feedparser
import subprocess
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. Configuration & AI Setup
try:
    with open("config.json") as f:
        config = json.load(f)
except FileNotFoundError:
    print("❌ Error: config.json file missing!")
    exit(1)

genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
ai_model = genai.GenerativeModel('gemini-pro')

# 2. Viral Metadata Generator
def get_ai_metadata(original_title):
    try:
        prompt = f"Write a viral YouTube Shorts title (under 60 chars) and a brief description with 5 hashtags for: {original_title}. Format: Line1: Title, Line2+: Description."
        response = ai_model.generate_content(prompt)
        parts = response.text.strip().split('\n')
        title = parts[0].strip()
        description = "\n".join(parts[1:]).strip()
        return title[:100], description
    except Exception as e:
        print(f"⚠️ AI Metadata Error: {e}")
        return original_title[:100], "#shorts #trending"

# 3. YouTube Upload Function
def upload_to_youtube(file_path, title, description):
    token_json = os.environ.get('YT_TOKEN_JSON')
    if not token_json:
        raise ValueError("YT_TOKEN_JSON environment variable is missing!")

    creds_data = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_data)
    
    # Auto-refresh logic (GitHub Actions ke liye zaroori)
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "22", 
            "tags": ["shorts", "automation"]
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    request.execute()
    print(f"🚀 Success: {title} uploaded!")

# 4. Main Process
def main():
    for creator in config["channels"]:
        print(f"--- Checking {creator['name']} ---")
        feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={creator['channel_id']}")
        
        if not feed.entries: continue
        
        video_url = feed.entries[0].link
        video_title = feed.entries[0].title

        # Fast Download (Only 30s)
        subprocess.run(["yt-dlp", "-f", "mp4", "--download-sections", "*0-30", "-o", "temp.mp4", video_url])
        
        # FFmpeg Processing (Force overwrite with -y)
        subprocess.run(["ffmpeg", "-y", "-i", "temp.mp4", "-t", "30", "-c", "copy", "final.mp4"])

        ai_t, ai_d = get_ai_metadata(video_title)

        try:
            upload_to_youtube("final.mp4", ai_t, ai_d)
        except Exception as e:
            print(f"❌ Upload Error: {e}")

        # Cleanup
        for f in ["temp.mp4", "final.mp4"]:
            if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    main()
