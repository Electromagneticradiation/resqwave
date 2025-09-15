import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("UTUBE_KEY")

BASE_URL = "https://www.googleapis.com/youtube/v3"

def search_videos(query, max_results=5):
    # Search YouTube videos by keyword
    url = f"{BASE_URL}/search?part=snippet&q={query}&type=video&maxResults={max_results}&key={API_KEY}"
    resp = requests.get(url).json()
    videos = []
    for item in resp.get("items", []):
        videos.append({
            "videoId": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "published": item["snippet"]["publishedAt"]
        })
    return videos

def fetch_comments(video_id, limit=10):
    # Fetch top-level comments from a YouTube video
    url = f"{BASE_URL}/commentThreads?part=snippet&videoId={video_id}&maxResults={limit}&key={API_KEY}"
    resp = requests.get(url).json()
    comments = []
    for item in resp.get("items", []):
        c = item["snippet"]["topLevelComment"]["snippet"]
        comments.append({
            "platform": "youtube",
            "videoId": video_id,
            "author": c["authorDisplayName"],
            "content": c["textDisplay"],
            "likes": c["likeCount"],
            "published": c["publishedAt"]
        })
    return comments

if __name__ == "__main__":
    # Example: scrape for cyclone-related videos in India
    videos = search_videos("cyclone India 2025", max_results=2)
    for v in videos:
        print(f"Fetching comments for video: {v['title']}")
        comments = fetch_comments(v["videoId"], limit=5)
        for c in comments:
            print(c)
