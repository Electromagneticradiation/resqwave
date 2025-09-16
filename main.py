import pymongo
from datetime import datetime, timezone
from redtel import scrape_reddit_search, scrape_telegram_channel
from utube import search_videos, fetch_comments
import random
from transformers import pipeline

LOCATIONS = [
    "Andhra Pradesh", "Odisha", "West Bengal", "Kerala", "Tamil Nadu",
    "Chennai", "Mumbai", "Kolkata", "Visakhapatnam", "Goa",
    "Andaman", "Nicobar", "Gujarat", "Puducherry", "Lakshadweep"
]

HAZARDS = ["cyclone", "flood", "storm", "heavy rain", "tsunami", "seawater intrusion"]

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def extract_location(text):
    for loc in LOCATIONS:
        if loc.lower() in text.lower():
            return loc
    return None

def extract_hazard(text):
    for hz in HAZARDS:
        if hz in text.lower():
            return hz
    return None 

def enrich_post(post, source="reddit"):
    loc = extract_location(post["content"])
    haz = extract_hazard(post["content"])
    if not loc:
        loc = random.choice(LOCATIONS)
    if not haz:
        haz = random.choice(HAZARDS)

    return {
        "source": source,
        "content": post["content"],
        "hazard_type": haz,
        "location": loc,
        "date": post.get("date") or datetime.now(timezone.utc).isoformat()
    }

# --- LLM SUMMARY ---

def llm_summary(posts): 
    text = "\n".join([p["content"][:200] for p in posts[:30]])
    max_chunk = 1000
    chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
        summaries.append(summary)
    return " ".join(summaries)

# --- INSERT INTO DB ---

def save_posts(col, posts, source):
    enriched = [enrich_post(p, source) for p in posts]
    if enriched:
        col.insert_many(enriched)
    return enriched

def main():
    # Connect to MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["resqwave"]
    col = db["social_posts"]
    summary_col = db["summary_posts"] 

    all_posts = []

    # --- Reddit ---
    reddit_posts = scrape_reddit_search(
        keywords=["flood alert", "tsunami warning"],
        subreddits=["bangalore", "mumbai", "chennai", "kolkata"],
        limit=1
    )
    enriched_reddit = save_posts(col, reddit_posts, "reddit")
    all_posts.extend(enriched_reddit)

    # --- Telegram ---
    hazard_keywords = [ "flood", "cyclone", "tsunami" ]
    telegram_posts = scrape_telegram_channel(
        "coastalalert",
        limit=20,
        keywords=hazard_keywords
    )
    enriched_telegram = save_posts(col, telegram_posts, "telegram")
    all_posts.extend(enriched_telegram)

    # --- YouTube ---
    videos = search_videos("karnataka flood today", max_results=2)
    for v in videos:
        comments = fetch_comments(v["videoId"], limit= 2)
        for c in comments:
            # normalize YouTube comment to match enrich_post expectations
            post_for_enrich = {
                "content": c["content"],
                "date": c.get("published")  # use published date from YouTube
            }
            enriched_comment = save_posts(col, [post_for_enrich], "youtube")
            all_posts.extend(enriched_comment)

     # --- LLM summary ---
    if all_posts:
        summary_text = llm_summary(all_posts)
        summary_doc = {
            "summary": summary_text,
            "date": datetime.now(timezone.utc).isoformat(),
            "num_posts": len(all_posts)
        }
        summary_col.insert_one(summary_doc)
                               
    print("Data inserted into MongoDB successfully.")

if __name__ == "__main__":
    main()
