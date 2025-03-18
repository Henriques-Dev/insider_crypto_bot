def generate_signal_message(symbol, price, time, action):
    return f"""
    🚨 *ALERTA DE TRADING* 🚨
    • Moeda: {symbol}
    • Preço Atual: ${price:.2f}
    • Horário: {time}
    • Ação Recomendada: {action}
    • _Análise automática gerada pelo robô_
    """


    class MessageTemplates:
    @staticmethod
    def alert_template(memecoin, action):
        return f"Alerta: {action} {memecoin.name}!"