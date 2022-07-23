from bots_ai.turn_state import BotAI


class BotAISpectator:
    def __init__(self, bot: BotAI, limit: int = 1):
        self.bot = bot
        self.limit = limit

    def get_fields(self, player_name: str):
        """return list of tree leaves limited by `limit` param and total leaves amount"""
        fields = self.bot.get_fields(player_name)
        return fields[:self.limit], len(fields)
