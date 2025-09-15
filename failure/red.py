import requests
from datetime import datetime

def scrape_red(key, limit = 10):
    url = "https://api.pushshift.io/reddit/search/submission"
    params = {
        "q": key,
        "size": limit,
        "sort": "desc",
        "sort_type": "created_utc",
        "subreddit": "india",
    }
    r = requests.get(url, params = params)
    data = r.json().get("data", [] )
    results = []
    for post in data:
        results.append({
            "platform": "reddit",
            "id": post.get("id"),
            "content": post.get("title"),
            "url": f"https://reddit.com{post.get('permalink')}",
            "created": datetime.datetime.utcfromtimestamp(post["created_utc"]),
        })
    return results

print(scrape_red("flood", limit = 5))
