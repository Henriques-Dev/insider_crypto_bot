import os
import pytest
import asyncio
from dotenv import load_dotenv
from analysis.social_api import SocialAPI

load_dotenv()  # Carrega variáveis para os testes

@pytest.fixture
async def social_api():
    # Fixture assíncrona com limpeza adequada
    api = SocialAPI()
    yield api
    await api.telegram_app.shutdown()

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )

@pytest.mark.asyncio
async def test_twitter(social_api):
    """Testa a coleta de dados do Twitter"""
    tweets = await asyncio.to_thread(
        social_api.get_twitter_mentions, 
        "SOL", 
        2
    )
    assert len(tweets) <= 2, "Deve retornar até 2 tweets"
    assert all(isinstance(tweet, dict) for tweet in tweets), "Formato inválido"

@pytest.mark.asyncio
async def test_reddit(social_api):
    """Testa a coleta de dados do Reddit"""
    posts = await asyncio.to_thread(
        social_api.get_reddit_posts,
        "Solana",
        1
    )
    assert len(posts) <= 1, "Deve retornar até 1 post"
    assert all("title" in post for post in posts), "Dados incompletos"

@pytest.mark.asyncio
async def test_telegram(social_api):
    """Testa a coleta de mensagens do Telegram"""
    try:
        messages = await asyncio.wait_for(
            social_api.get_telegram_messages("@test_channel", 1),
            timeout=15.0
        )
        assert isinstance(messages, list), "Deve retornar uma lista"
        assert len(messages) <= 1, "Deve respeitar o limite"
        
    except asyncio.TimeoutError:
        pytest.fail("Timeout excedido na coleta do Telegram")