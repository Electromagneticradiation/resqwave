import feedparser

def scrape_tele(channel, limit = 5):
    url = f"https://rsshub.app/telegram/channel/{channel}"
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:limit]:
        results.append({
            "platform": "telegram",
            "id": entry.id,
            "content": entry.title + " " + entry.get("summary", ""),
            "url": entry.link,
            "published": entry.published,
        })
    return results

if __name__ == "__main__":
    print(scrape_tele("durov", limit = 3))
