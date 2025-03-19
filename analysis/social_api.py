import os
import asyncio
from typing import List, Dict
from dotenv import load_dotenv
import tweepy
import praw
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from telegram.ext import ContextTypes

load_dotenv()

class SocialAPI:
    def __init__(self):
        # Twitter Client
        self.twitter_client = tweepy.Client(
            bearer_token=os.getenv("TWITTER_API_KEY")
        )
        
        # Reddit Client
        self.reddit_client = praw.Reddit(
            client_id=os.getenv("REDDIT_API_KEY"),
            client_secret=os.getenv("REDDIT_API_SECRET"),
            user_agent="memecoin-monitor/1.0"
        )

        # Telegram Client (Versão 20.x+)
        self.telegram_app = ApplicationBuilder()\
            .token(os.getenv("TELEGRAM_API_KEY"))\
            .build()

    def get_twitter_mentions(self, coin: str, limit: int = 100) -> List[Dict]:
        """Coleta menções de memecoins no Twitter"""
        try:
            query = f"#{coin} OR ${coin} lang:en -is:retweet"
            tweets = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=limit,
                tweet_fields=["created_at", "public_metrics"]
            )
            
            return [{
                "id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at,
                "likes": tweet.public_metrics["like_count"],
                "retweets": tweet.public_metrics["retweet_count"]
            } for tweet in tweets.data]

        except tweepy.TweepyException as e:
            print(f"Erro Twitter: {e}")
            return []

    def get_reddit_posts(self, coin: str, limit: int = 50) -> List[Dict]:
        """Coleta posts relevantes no Reddit"""
        try:
            subreddits = ["CryptoCurrency", "solana", "memecoin"]
            results = []
            
            for sub in subreddits:
                submissions = self.reddit_client.subreddit(sub).search(
                    query=coin,
                    limit=limit//len(subreddits)
                )
                
                for submission in submissions:
                    results.append({
                        "id": submission.id,
                        "title": submission.title,
                        "score": submission.score,
                        "created_utc": submission.created_utc,
                        "url": submission.url
                    })
            
            return results

        except praw.exceptions.PRAWException as e:
            print(f"Erro Reddit: {e}")
            return []

    async def get_telegram_messages(self, channel_id: str, limit: int = 50) -> List[Dict]:
        """Coleta mensagens de canais do Telegram (Assíncrono)"""
        try:
            messages = []
            
            async def collect_messages(update: Update, context):
                if len(messages) < limit:
                    messages.append({
                        "id": update.message.message_id,
                        "text": update.message.text,
                        "date": update.message.date
                    })

            self.telegram_app.add_handler(
                MessageHandler(filters.TEXT, collect_messages)
            )

            await self.telegram_app.initialize()
            await self.telegram_app.start_polling()
            await asyncio.sleep(10)  # Tempo de coleta
            await self.telegram_app.stop()
            
            return messages

        except Exception as e:
            print(f"Erro Telegram: {e}")
            return []