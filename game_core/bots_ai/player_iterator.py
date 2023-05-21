from game_core.bots_ai.field_handler.player_state import PlayerState


class PlayerIterator:
    def __init__(self, players: dict[str, PlayerState], current_player_idx: int = 0):
        self.is_host_turn = False
        self._players = players
        self._players_names = list(self._players.keys())
        self._current_player_idx = current_player_idx

    def get_current(self):
        return self._players_names[self._current_player_idx]

    def __next__(self):
        next_player_idx = (self._current_player_idx + 1) % len(self._players_names)
        next_player = self._players_names[next_player_idx]
        if next_player_idx < self._current_player_idx:
            self.is_host_turn = True
        self._current_player_idx = next_player_idx
        if not self._players.get(next_player).stats.is_alive:
            self.__next__()
        return next_player

    def __iter__(self):
        return self
