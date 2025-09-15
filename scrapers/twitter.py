import snscrape.modules.twitter as snstwt
from datetime import datetime, timezone, timedelta
#import certifi
#import ssl

#ssl_context = ssl.create_default_context(cafile=certifi.where())

# key = terms to look for in tweets
# lim = max num of tweets to return
# min = how many min ago to look from
# returns list of dicts with tweet info

def scrapetwt(key, lim = 100, min = 15):
    
    time = (datetime.now(timezone.utc) - timedelta(minutes = min)).strftime("%Y-%m-%d_%H:%M:%S_UTC")
    query = "(" + " OR ".join(key) + f") since:{time}"

    tweets = []
    # enumerate just adds index to items. we use it for limiting
    for i, tweet in enumerate(snstwt.TwitterSearchScraper(query).get_items()):
        if i >= lim:
            break
        tweets.append({
            "content": tweet.content,
            "platform": "Twitter",
            "date": tweet.date,
            "user": tweet.user.username,
            "url": tweet.url,
            "geotag": tweet.coordinates if tweet.coordinates else None,
            "likes": tweet.likeCount,
            "shares": tweet.retweetCount
        })

    return tweets

# testing

if __name__ == "__main__":
    print(scrapetwt(["snow"], 5, 60))
