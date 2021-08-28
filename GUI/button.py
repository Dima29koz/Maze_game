import pygame


class Button:
    def __init__(self, screen, position, text, action, size):
        self.is_active = False
        self.is_available = True
        self.screen = screen
        self.x, self.y = position
        self.text = text
        self.action = action
        self.size = size

        font = pygame.font.SysFont("Arial", size*2//3)
        self.text_render = font.render(text, True, (255, 255, 255))
        self.place = self.text_render.get_rect(center=(self.x + size // 2, self.y + size // 2))
        self.area = pygame.Rect((self.x, self.y, self.size, self.size))

    def get(self):
        return self.area

    def active(self):
        return self.action

    def draw(self):
        pygame.draw.rect(self.screen, 'red' if not self.is_active else 'green', self.area)
        self.screen.blit(self.text_render, self.place)




