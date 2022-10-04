from bots_ai.core import BotAI


class BotAISpectator:
    def __init__(self, bot: BotAI, limit: int = 1):
        self.bot = bot
        self.limit = limit

    def get_fields(self, player_name: str):
        """return list of tree leaves limited by `limit` param and total leaves amount"""
        leaves = self.bot.players.get(player_name).get_leaf_nodes()
        leaves = [leaf.get_current_data() for leaf in leaves]
        return leaves[:self.limit], len(leaves)

    def get_real_spawn_leaves(self, player_name: str):
        leaves = self.bot.players.get(player_name).get_real_spawn_leaves()
        leaves = [leaf.get_current_data() for leaf in leaves]
        return leaves[:self.limit], len(leaves)

    def get_other_players(self, player_name: str):
        other_players = list(self.bot.players.keys())
        other_players.remove(player_name)
        return other_players

    def get_compatible_leaves(self, player_name: str, other_player: str, limit=None):
        limit = limit if limit else self.limit
        leaves = self.bot.players.get(other_player).get_compatible_leaves(player_name)
        leaves = [leaf.get_current_data() for leaf in leaves]
        return leaves[:limit], len(leaves)
