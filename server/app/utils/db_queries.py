from server.app.main.models import GameRoom


def get_not_ended_room_by_name(room_name: str) -> GameRoom | None:
    """returns not ended game room by name if room exists"""
    return GameRoom.query.filter_by(name=room_name, is_ended=False).first()


def get_room_by_id(room_id: int) -> GameRoom | None:
    """returns game room by id if room exists"""
    return GameRoom.query.filter_by(id=room_id).first()


def get_user_won_games_amount(user_id: int) -> int:
    """returns amount of user won games"""
    return GameRoom.query.filter_by(winner_id=user_id).count()
