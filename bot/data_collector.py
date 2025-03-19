import time
from analysis.social_api import SocialAPI


#Serviço de coleta contínua
class SocialDataCollector:
    def __init__(self):
        self.social = SocialAPI()

    def start_monitoring(self):
        while True:
            try:
                # Coleta a cada 5 minutos
                self._collect_twitter_data()
                self._collect_reddit_data()
                self._collect_telegram_data()
                time.sleep(300)

            except KeyboardInterrupt:
                break

    def _collect_twitter_data(self):
        tweets = self.social.get_twitter_mentions("SOL", 100)
        # Salva no banco de dados ou envia para fila de processamento

    def _collect_reddit_data(self):
        posts = self.social.get_reddit_posts("Solana", 50)
        # Mesmo processo de armazenamento

    def _collect_telegram_data(self):
        messages = self.social.get_telegram_messages("@canal_memecoins", 50)
        # Mesmo processo de armazenamento