class GuiConfig:
    FPS = 60
    SHOW_FPS = True
    RES = WIDTH, HEIGHT = 1920, 1080  # window size
    TILE = 50  # tile size for interactive map
    BTN_X = 0  # pos_x bnt block
    BTN_Y = 400  # pos_y bnt block
    DIST = 10  # margin between leaves
    LIMIT = 20  # amount of displaying leaves
    TILE_LEAF = 16
    BG_COLOR = None
    # BG_COLOR = (255, 255, 255)


class BotAIColors:
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    REAL = (165, 255, 190)  # node.is_real
