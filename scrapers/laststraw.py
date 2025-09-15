import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from datetime import datetime, timezone
import sys
import html

UA = "ResQwaveBot (for collecting ocean hazards ground intel) Python/requests"

def to_utc_iso(value):
    """Normalize timestamps to timezone-aware UTC ISO strings."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # epoch seconds (Pushshift/Reddit use seconds)
        if value > 1e12:  # milliseconds heuristic
            value = value / 1000.0
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    if isinstance(value, str):
        try:
            dt = dateparser.parse(value)
        except Exception:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return None

def unify_post(content, platform, date_iso=None, author=None, url=None, extra=None):
    return {
        "content": content,
        "platform": platform,
        "date": to_utc_iso(date_iso) or datetime.now(timezone.utc).isoformat(),
        "author": author,
        "url": url,
        "meta": extra or {}
    }

# ----------------- Reddit via public JSON endpoints -----------------
def scrape_reddit_search(keywords, subreddits=None, limit=25):
    """
    Uses reddit.com search JSON endpoints (no OAuth).
    keywords: list or string (if list, they will be OR-joined).
    subreddits: list, string with + (multi-subreddit), or None
    """
    q = keywords if isinstance(keywords, str) else " OR ".join(keywords)
    headers = {"User-Agent": UA}
    posts = []

    # normalize subreddits
    if subreddits:
        if isinstance(subreddits, str):
            subs = subreddits.split("+")
        elif isinstance(subreddits, (list, tuple)):
            subs = []
            for s in subreddits:
                subs.extend(s.split("+"))
        else:
            subs = []
    else:
        subs = [None]

    for sub in subs:
        if sub:
            url = f"https://www.reddit.com/r/{sub}/search.json"
            params = {
                "q": q,
                "restrict_sr": True,
                "sort": "new",
                "limit": limit,
                "include_over_18": "on"
            }
        else:
            url = "https://www.reddit.com/search.json"
            params = {
                "q": q,
                "sort": "new",
                "limit": limit,
                "include_over_18": "on"
            }

        try:
            r = requests.get(url, params=params, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[Reddit:{sub or 'all'}] request failed:", e)
            continue

        children = data.get("data", {}).get("children", [])
        for c in children:
            d = c.get("data", {})
            title = d.get("title") or ""
            selftext = d.get("selftext") or ""
            text = (title + "\n" + selftext).strip()
            created = d.get("created_utc")
            url_post = "https://www.reddit.com" + d.get("permalink") if d.get("permalink") else d.get("url")
            author = d.get("author")
            posts.append(unify_post(
                text, "reddit",
                date_iso=created,
                author=author,
                url=url_post,
                extra={
                    "subreddit": d.get("subreddit"),
                    "id": d.get("id"),
                    "score": d.get("score"),
                    "num_comments": d.get("num_comments")
                }
            ))

    return posts
# ----------------- Telegram scraping via t.me/s/<channel> -----------------
def scrape_telegram_channel(channel, limit=25):
    """
    Scrape public telegram channel via t.me/s/<channel> HTML.
    Returns list of unified posts.
    """
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": UA}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        html_text = r.text
    except Exception as e:
        print(f"[Telegram] HTTP error for {channel}:", e)
        return []

    soup = BeautifulSoup(html_text, "html.parser")
    # Telegram message blocks
    msgs = soup.select("div.tgme_widget_message")
    results = []
    for m in msgs[:limit]:
        # text
        text_node = m.select_one("div.tgme_widget_message_text")
        content = ""
        if text_node:
            # preserve line breaks but remove extra spaces
            content = "\n".join([line.strip() for line in text_node.strings])
            content = html.unescape(content)
        # date/time: anchor with class 'tgme_widget_message_date' has a time tag
        date_iso = None
        date_anchor = m.select_one("a.tgme_widget_message_date")
        if date_anchor:
            time_tag = date_anchor.find("time")
            if time_tag and time_tag.has_attr("datetime"):
                date_iso = time_tag["datetime"]
        # post id and url
        post_url = None
        post_id = None
        if date_anchor and date_anchor.has_attr("href"):
            href = date_anchor["href"]  # e.g. /channel/123 or /channel/123
            # sometimes href like '/channelname/123'
            parts = href.strip("/").split("/")
            if len(parts) >= 2 and parts[-1].isdigit():
                post_id = parts[-1]
        # fallback: some messages have 'data-post' attributes
        if not post_id:
            try:
                post_id = m["data-post"]
            except Exception:
                post_id = None
        if post_id:
            post_url = f"https://t.me/{channel}/{post_id}"

        # author: sometimes present in header
        author = None
        author_tag = m.select_one("a.tgme_widget_message_from_author")
        if author_tag:
            author = author_tag.text.strip()

        results.append(unify_post(content or "", "telegram", date_iso=date_iso, author=author, url=post_url, extra={"channel": channel, "post_id": post_id}))
    return results

# ----------------- CLI usage -----------------
def pretty_print_list(l):
    for i, p in enumerate(l):
        print(f"--- {i+1} ---")
        print("platform:", p.get("platform"))
        print("date:", p.get("date"))
        print("author:", p.get("author"))
        print("url:", p.get("url"))
        print("content:", (p.get("content") or "")[:400])
        print("meta:", p.get("meta"))
        print()

if __name__ == "__main__":

    # Example usage:
    # python scrapers/laststraw.py reddit "flood cyclone" 10 india+news
    # python scrapers/laststraw.py telegram durov 5

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python scraper.py reddit <keywords> [limit] [subreddits(separated by plus (+)|optional)]")
        print("  python scraper.py telegram <channel> [limit]")
        sys.exit(1)

    backend = sys.argv[1].lower()
    if backend == "reddit":
        keywords = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 25
        subreddits = None
        if len(sys.argv) > 4:
            subreddits = sys.argv[4].split(",")
        out = scrape_reddit_search(keywords.split(), subreddits=subreddits, limit=limit)
        pretty_print_list(out)
    elif backend == "telegram":
        channel = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        out = scrape_telegram_channel(channel, limit=limit)
        pretty_print_list(out)
    else:
        print("Unknown backend")
