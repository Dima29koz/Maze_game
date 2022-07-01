from bots_ai.turn_state import BotAI


class BotAISpectator:
    def __init__(self, bot: BotAI, limit: int = 1):
        self.bot = bot
        self.limit = limit

    def get_fields(self):
        fields = self.bot.get_fields()
        return fields[:self.limit], len(fields)
