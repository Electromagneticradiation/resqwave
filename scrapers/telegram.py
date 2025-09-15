from telethon import TelegramClient
from datetime import datetime, timezone

api_id = 
api_hash = 
client = TelegramClient('resqwave_session', api_id, api_hash)

async def scrape_channel(channel, limit=10):
    posts = []
    async with client:
        async for message in client.iter_messages(channel, limit=limit):
            posts.append({
                "content": message.text,
                "metadata": {
                    "platform": "telegram",
                    "author": str(message.sender_id),
                    "date": message.date.isoformat() if message.date else None,
                    "geo": None,
                    "url": f"https://t.me/{channel}/{message.id}"
                }
            })
    return posts
