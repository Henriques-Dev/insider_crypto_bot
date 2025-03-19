import logging
from logger import setup_logger
from bot.meme_bot import MemeBot

def main():
    setup_logger()
    bot = MemeBot()
    bot.start_monitoring()

if __name__ == "__main__":
    main()