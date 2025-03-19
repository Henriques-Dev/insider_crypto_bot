import asyncio
from typing import Dict, List
from analysis.social_api import SocialAPI
from memecoins.memecoin_manager import MemecoinManager
from strategies.entry_exit_strategy import TradingStrategy

class MemeBot:
    def __init__(self):
        self.social_api = SocialAPI()
        self.coin_manager = MemecoinManager()
        self.trading_strategy = TradingStrategy()
        self.monitoring_interval = 300  # 5 minutos
        self.active_coins = []
        self.running = False

    async def start_monitoring(self):
        """Loop principal assíncrono de monitoramento"""
        self.running = True
        try:
            # Inicia serviços em paralelo
            monitoring_tasks = [
                asyncio.create_task(self._monitoring_cycle()),
                asyncio.create_task(self.social_api.telegram_listener())
            ]
            
            await asyncio.gather(*monitoring_tasks)
            
        except asyncio.CancelledError:
            await self._shutdown()

    async def _monitoring_cycle(self):
        """Ciclo principal de coleta e análise"""
        while self.running:
            await self._refresh_memecoin_list()
            await self._collect_social_data()
            await self._analyze_and_execute()
            await asyncio.sleep(self.monitoring_interval)

    async def _refresh_memecoin_list(self):
        """Atualiza lista de memecoins de forma assíncrona"""
        self.active_coins = await asyncio.to_thread(
            self.coin_manager.get_active_memecoins
        )
        print(f"Monitorando {len(self.active_coins)} memecoins")

    async def _collect_social_data(self):
        """Coleta paralela de dados usando threads"""
        for coin in self.active_coins:
            # Coleta Twitter em thread separada
            coin.twitter_data = await asyncio.to_thread(
                self.social_api.get_twitter_mentions,
                coin.symbol,
                100
            )
            
            # Coleta Reddit em thread separada
            coin.reddit_data = await asyncio.to_thread(
                self.social_api.get_reddit_posts,
                coin.name,
                50
            )

    async def _analyze_and_execute(self):
        """Processamento paralelo de análise"""
        tasks = []
        for coin in self.active_coins:
            task = asyncio.create_task(
                self._process_coin(coin)
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)

    async def _process_coin(self, coin):
        """Executa análise e trading para uma moeda específica"""
        analysis = await asyncio.to_thread(
            self.trading_strategy.analyze,
            coin_data=coin,
            social_data={
                'twitter': coin.twitter_data,
                'reddit': coin.reddit_data,
                'telegram': await self.social_api.get_telegram_messages()
            }
        )
        
        if analysis['action'] != 'hold':
            await self._execute_trade(coin, analysis)

    async def _execute_trade(self, coin, analysis: Dict):
        """Execução assíncrona de ordens"""
        print(f"Executando {analysis['action']} em {coin.symbol}")
        # Exemplo de execução assíncrona:
        # await self.exchange_api.async_create_order(...)

    async def _shutdown(self):
        """Desligamento seguro de recursos"""
        print("\nDesligando o robô...")
        await asyncio.to_thread(self.coin_manager.save_state)
        await self.social_api.telegram_app.shutdown()
        self.running = False

if __name__ == "__main__":
    bot = MemeBot()
    
    try:
        asyncio.run(bot.start_monitoring())
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário")