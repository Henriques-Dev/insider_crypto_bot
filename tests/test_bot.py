import unittest
from bot.meme_bot import MemeBot

class TestMemeBot(unittest.TestCase):
    def test_start_monitoring(self):
        bot = MemeBot()
        self.assertIsNone(bot.start_monitoring())