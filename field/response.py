from field.cell import *
from field.wall import *


class RespHandler:
    def __init__(self, response):
        self.response = response

    def get_info(self):
        return self.response


class RespHandlerSkip(RespHandler):
    pass


class RespHandlerSwap(RespHandler):
    pass


class RespHandlerShootBow(RespHandler):
    pass


class RespHandlerBombing(RespHandler):
    pass


class RespHandlerMoving(RespHandler):
    pass
