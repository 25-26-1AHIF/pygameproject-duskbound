import pygame


def make_font(size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont("georgia", size, bold=bold)


# KI-Anfang
# KI: ChatGPT
# prompt: Erstelle UI-Funktionen für ein Pygame-Spiel, die zentrierten Text mit schwarzer Outline, klickbare Buttons mit Hover-Effekt und ein HUD mit Herzen, Kristallen, Level und Score zeichnen.
def draw_center_text(surface, text, font, y, color=(240, 240, 240), outline=True):
    img = font.render(text, True, color)
    x = surface.get_width() // 2 - img.get_width() // 2

    if outline:
        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            shadow = font.render(text, True, (12, 10, 25))
            surface.blit(shadow, (x + ox, y + oy))

    surface.blit(img, (x, y))


def draw_button(surface, rect, text, font, mouse_pos):
    hover = rect.collidepoint(mouse_pos)

    fill = (80, 55, 130) if hover else (35, 30, 60)
    border = (230, 220, 255) if hover else (120, 90, 180)

    pygame.draw.rect(surface, (12, 10, 25), rect.inflate(8, 8), border_radius=12)
    pygame.draw.rect(surface, fill, rect, border_radius=10)
    pygame.draw.rect(surface, border, rect, 3, border_radius=10)

    label = font.render(text, True, (255, 255, 255))
    surface.blit(
        label,
        (
            rect.centerx - label.get_width() // 2,
            rect.centery - label.get_height() // 2,
        ),
    )

    return hover


def draw_hud(surface, hp, level_number, collected, total, score, heart_image=None):
    font = make_font(22, True)

    for i in range(hp):
        if heart_image:
            surface.blit(heart_image, (22 + i * 36, 18))
        else:
            pygame.draw.circle(surface, (235, 60, 90), (34 + i * 36, 35), 12)

    def outlined_text(text, color, pos):
        x, y = pos

        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            shadow = font.render(text, True, (10, 10, 25))
            surface.blit(shadow, (x + ox, y + oy))

        text_img = font.render(text, True, color)
        surface.blit(text_img, (x, y))

    outlined_text(f"Kristalle: {collected}/{total}", (245, 245, 255), (22, 58))
    outlined_text(f"Level: {level_number}/5", (245, 245, 255), (790, 18))
    outlined_text(f"Score: {score}", (245, 245, 255), (790, 48))
# KI-Ende