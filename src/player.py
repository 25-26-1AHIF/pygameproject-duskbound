import pygame
from settings import GRAVITY, PLAYER_JUMP, PLAYER_SPEED

class Player:
    def __init__(self, x:int, y:int, sprites=None):
        self.rect = pygame.Rect(x, y, 42, 58)
        self.pos = pygame.Vector2(float(x), float(y))
        self.velocity = pygame.Vector2(0,0)
        self.facing = 1
        self.on_ground = False
        self.max_hp = 3
        self.hp = 3
        self.invincible_timer = 0
        self.jump_buffer_timer = 0
        self.coyote_timer = 0
        self.max_jumps = 2
        self.jumps_used = 0
        self.sprites = sprites or {}
        self.anim_time = 0.0
        self.attack_timer = 0
        self.attack_hit_done = False
        self.current_action = "idle"

    def attack_rect(self):
        if self.attack_timer <= 0:
            return pygame.Rect(0, 0, 0, 0)
        if self.facing == 1:
            return pygame.Rect(self.rect.right - 6, self.rect.y + 8, 54, 44)
        return pygame.Rect(self.rect.left - 48, self.rect.y + 8, 54, 44)

    def start_attack(self):
        if self.attack_timer <= 0:
            self.attack_timer = 16
            self.attack_hit_done = False
            self.anim_time = 0.0

    # KI-Anfang
    # KI: ChatGPT
    # prompt: Player Movement mit Kollision, Coyote-Time, Jump-Buffer, Doppelsprung und Float-Positionen umsetzen.
    def update(self, keys, platforms):
        jumped = False
        dx = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -PLAYER_SPEED
            self.facing = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = PLAYER_SPEED
            self.facing = 1

        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= 1
        if self.on_ground:
            self.coyote_timer = 8
        elif self.coyote_timer > 0:
            self.coyote_timer -= 1

        self.velocity.x = dx
        self.velocity.y = min(self.velocity.y + GRAVITY, 18)

        self.pos.x += self.velocity.x
        self.rect.x = round(self.pos.x)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.velocity.x > 0:
                    self.rect.right = p.left
                elif self.velocity.x < 0:
                    self.rect.left = p.right
                self.pos.x = self.rect.x

        self.pos.y += self.velocity.y
        self.rect.y = round(self.pos.y)
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p):
                if self.velocity.y > 0:
                    self.rect.bottom = p.top
                    self.velocity.y = 0
                    self.on_ground = True
                elif self.velocity.y < 0:
                    self.rect.top = p.bottom
                    self.velocity.y = 0
                self.pos.y = self.rect.y

        if self.on_ground:
            self.jumps_used = 0

        can_ground = self.on_ground or self.coyote_timer > 0
        can_air = (not self.on_ground) and self.jumps_used < self.max_jumps
        if self.jump_buffer_timer > 0 and (can_ground or can_air):
            self.velocity.y = PLAYER_JUMP
            self.on_ground = False
            self.jump_buffer_timer = 0
            self.coyote_timer = 0
            self.jumps_used += 1
            jumped = True

        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.attack_timer > 0:
            self.attack_timer -= 1

        if self.attack_timer > 0:
            self.current_action = "attack"
            self.anim_time += 0.25
        elif not self.on_ground:
            self.current_action = "jump"
            self.anim_time += 0.12
        elif abs(self.velocity.x) > 0.15:
            self.current_action = "run"
            self.anim_time += 0.20
        else:
            self.current_action = "idle"
            self.anim_time += 0.10

        return jumped
    # KI-Ende

    def jump(self):
        self.jump_buffer_timer = 10

    def take_damage(self, direction):
        if self.invincible_timer > 0:
            return False
        self.hp -= 1
        self.invincible_timer = 70
        self.velocity.x = -direction * 6
        self.velocity.y = -7
        return True

    def _current_image(self):
        frames = self.sprites.get(self.current_action) or self.sprites.get('idle', [])
        if not frames:
            return None
        frame_index = int(self.anim_time) % len(frames)
        return frames[frame_index]

    def draw(self, surface, camera_x):
        if self.invincible_timer > 0 and self.invincible_timer % 10 < 5:
            return
        img = self._current_image()
        if img:
            draw_img = pygame.transform.flip(img, True, False) if self.facing == -1 else img
            draw_rect = draw_img.get_rect(midbottom=(self.rect.centerx - camera_x, self.rect.bottom + 4))
            surface.blit(draw_img, draw_rect)
        else:
            pygame.draw.rect(surface, (60,60,120), self.rect.move(-camera_x, 0), border_radius=8)