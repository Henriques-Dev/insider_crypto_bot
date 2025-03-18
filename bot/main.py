import logging
from logger import get_logger
from bot.meme_bot import MemeBot

def main():
    setup_logging()
    bot = MemeBot()
    bot.start_monitoring()

if __name__ == "__main__":
    main()