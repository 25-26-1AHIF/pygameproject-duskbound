import pygame

class Enemy:
    def __init__(self, enemy_id, x, y, left_limit, right_limit, sprites=None, hp=1, kind="mini"):
        self.id = enemy_id
        self.kind = kind
        self.width = 38 if kind == "mini" else 44
        self.height = 52 if kind == "mini" else 60
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.pos = pygame.Vector2(float(x), float(y))

        # Gegner auf Boden setzen. Bodenoberkante ist y=500.
        self.rect.bottom = 500
        self.pos.y = self.rect.y

        self.left_limit = left_limit
        self.right_limit = right_limit
        self.speed = 1.35 if kind == "mini" else 1.05
        self.direction = -1
        self.alive = True
        self.hp = hp
        self.max_hp = hp
        self.sprites = sprites or []
        self.anim_time = 0.0
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.attack_hit_done = False

    def attack_rect(self):
        if self.attack_timer <= 0:
            return pygame.Rect(0, 0, 0, 0)
        width = 46 if self.kind == "mini" else 58
        if self.direction >= 0:
            return pygame.Rect(self.rect.right - 2, self.rect.y + 10, width, 36)
        return pygame.Rect(self.rect.left - width + 2, self.rect.y + 10, width, 36)

    # KI-Anfang
    # KI: ChatGPT
    # prompt: Gegner-KI mit Nähe-Erkennung, Angriff und Bodenfixierung erstellen.
    def update(self, player_rect):
        if not self.alive:
            return

        self.rect.bottom = 500
        self.pos.y = self.rect.y

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.attack_timer > 0:
            self.attack_timer -= 1
            return

        horizontal_distance = player_rect.centerx - self.rect.centerx
        vertical_close = abs(player_rect.centery - self.rect.centery) < 42

        if abs(horizontal_distance) < 72 and vertical_close and self.attack_cooldown == 0:
            self.direction = 1 if horizontal_distance >= 0 else -1
            self.attack_timer = 20
            self.attack_cooldown = 48
            self.attack_hit_done = False
            return

        self.pos.x += self.speed * self.direction
        self.rect.x = round(self.pos.x)

        if self.rect.left <= self.left_limit:
            self.rect.left = self.left_limit
            self.pos.x = self.rect.x
            self.direction = 1

        if self.rect.right >= self.right_limit:
            self.rect.right = self.right_limit
            self.pos.x = self.rect.x
            self.direction = -1

        self.anim_time += 0.04
    # KI-Ende

    def take_hit(self, damage=1):
        if not self.alive:
            return False
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface, camera_x):
        if not self.alive:
            return

        img = self.sprites[int(self.anim_time) % len(self.sprites)] if self.sprites else None
        if img:
            draw_img = pygame.transform.flip(img, True, False) if self.direction < 0 else img

            # Optisch etwas tiefer zeichnen, weil das Sprite unten transparenten Rand hat.
            draw_rect = draw_img.get_rect(midbottom=(self.rect.centerx - camera_x, 516))
            surface.blit(draw_img, draw_rect)
        else:
            pygame.draw.rect(surface, (20, 20, 30), self.rect.move(-camera_x, 0), border_radius=8)

        if self.max_hp > 1:
            x = self.rect.x - camera_x
            y = self.rect.y - 10
            pygame.draw.rect(surface, (55, 15, 20), (x, y, 44, 6))
            pygame.draw.rect(surface, (220, 45, 70), (x, y, int(44 * self.hp / self.max_hp), 6))
