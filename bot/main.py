import logging
from logger.log_config import setup_logging
from bot.meme_bot import MemeBot
from analysis.social_api import SocialAPI
from memecoins.memecoin_manager import MemecoinAnalyzer

def main():
    # Inicializa componentes
    social = SocialAPI()
    analyzer = MemecoinAnalyzer()

    # Coleta dados sociais
    tweets = social.get_twitter_mentions("SOL", 100)
    reddit_posts = social.get_reddit_posts("Solana", 50)
    telegram_msgs = social.get_telegram_messages("@canal_memecoins", 50)

    # Processa dados
    analysis_results = analyzer.analyze_social_data(
        tweets, 
        reddit_posts,
        telegram_msgs
    )

    # Toma decisões de trading
    if analysis_results["buy_signal"]:
        execute_trade("buy", analysis_results)

if __name__ == "__main__":
    main()