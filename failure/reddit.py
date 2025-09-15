import praw
from datetime import datetime, timezone

reddit = praw.Reddit(
    client_id = 'Kooky_Key_9900',
    client_secret = 'L86fVDwZUAPUMLcsHs2azSYs3dmNnw',
    user_agent='resqwave_disaster_monitor'
)

def scrape_subreddit(subreddit_name, limit=10, keywords=None):
    posts = []
    subreddit = reddit.subreddit(subreddit_name)
    for submission in subreddit.new(limit=limit):
        text = submission.title + "\n" + submission.selftext
        if keywords and not any(k.lower() in text.lower() for k in keywords):
            continue
        posts.append({
            "content": text,
            "metadata": {
                "platform": "reddit",
                "author": submission.author.name if submission.author else None,
                "date": datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).isoformat(),
                "geo": None,
                "url": submission.url
            }
        })
    return posts
