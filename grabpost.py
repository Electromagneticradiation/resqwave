import pymongo
from datetime import datetime, timezone
from scrapers.laststraw import scrape_reddit_search
from scrapers.laststraw import scrape_telegram_channel
from scrapers.utube import search_videos, fetch_comments


def to_doc(item):
    """Normalize scraped item to Mongo schema."""
    return {
        "platform": item.get("platform"),
        "id": item.get("id"),
        "content": item.get("content"),
        "author": item.get("author"),
        "url": item.get("url"),
        "date": item.get("date", datetime.now(timezone.utc)),
        "meta": item.get("meta", {}),
        "inserted_at": datetime.now(timezone.utc),
    }


def main():
    # connect to Mongo
    client = pymongo.MongoClient("mongodb://localhost:27017/reqwave")
    db = client["resqwave"]
    col = db["social_posts"]

    # Reddit
    reddit_posts = scrape_reddit_search(
        keywords=["cyclone", "flood",],
        subreddits=["bangalore", "mumbai", "chennai", "kolkata"],
        limit=5
    )
    if reddit_posts:  # only insert if non-empty
        col.insert_many([to_doc(p) for p in reddit_posts])
    else:
        print("[Reddit] No posts found for given query.")

    # Telegram
    telegram_posts = scrape_telegram_channel("IndianExpress", limit=5)
    col.insert_many([to_doc(p) for p in telegram_posts])

    # YouTube (first find videos, then fetch comments)
    videos = search_videos("Cyclone India", max_results=2)
    for v in videos:
        comments = fetch_comments(v["videoId"], limit=5)
        for c in comments:
            c["meta"] = {"videoId": v["videoId"], "videoTitle": v["title"]}
            col.insert_one(to_doc(c))

    print("Data inserted into MongoDB successfully.")


if __name__ == "__main__":
    main()
