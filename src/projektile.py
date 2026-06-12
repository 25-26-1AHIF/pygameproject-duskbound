import pygame


class Projectile:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(x, y, 12, 12)
        self.direction = direction
        self.speed = 13
        self.alive = True

    def update(self):
        self.rect.x += self.speed * self.direction

    def is_off_screen(self, camera_x, screen_width, level_width):
        return True

    def draw(self, surface, camera_x):
        pass
