from GUI.spectator import GUI
from field.field import Field

FPS = 30
RES = WIDTH, HEIGHT = 1202, 600
TILE = 50
cols, rows = 5, 4

rules = {
    'generator_rules': {'rows': 4, 'cols': 5},
    'host_rules': {},
}

field = Field(rules=rules)
gui = GUI(FPS, RES, TILE, field)

gui.mainloop()
