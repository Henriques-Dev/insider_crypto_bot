import os
from dotenv import load_dotenv

load_dotenv()

API_KEYS = {
    #"dexscreener": os.getenv("DEXSCREENER_API_KEY"),
    "twitter": os.getenv("TWITTER_API_KEY"),
    "reddit": os.getenv("REDDIT_API_KEY"),
    "telegram": os.getenv("TELEGRAM_API_KEY"),
}