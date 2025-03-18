import logging
from logger.log_config import setup_logging
from bot.meme_bot import MemeBot

def main():
    setup_logging()
    bot = MemeBot()
    bot.start_monitoring()

if __name__ == "__main__":
    main()