"""initialization of socketIO eventHandlerNamespace"""

from ... import sio
from .game_room import GameRoomNamespace
from .game import GameNamespace

sio.on_namespace(GameRoomNamespace('/game_room'))
sio.on_namespace(GameNamespace('/game'))
