import json
from pathlib import Path
import pygame
from src.enemy import Enemy


# level dateien laden und spielobjekte initialisieren

class Level:
    def __init__(self, index, data, collected_ids=None, killed_enemy_ids=None, mini_enemy_sprites=None,
                 boss_enemy_sprites=None, background=None, heart_image=None, portal_image=None):
        self.index = index
        self.name = data["name"]
        self.width = data["width"]
        self.spawn = tuple(data["spawn"])
        self.background = background
        self.heart_image = heart_image
        self.portal_image = portal_image
        self.platforms = [pygame.Rect(*r) for r in data["platforms"]]
        self.spikes = [pygame.Rect(*r) for r in data["spikes"]]
        self.portal = pygame.Rect(data["portal"][0], data["portal"][1], 76, 96)

        if collected_ids is None:
            collected_ids = []
        else:
            collected_ids = collected_ids

        if killed_enemy_ids is None:
            killed_enemy_ids = []
        else:
            killed_enemy_ids = killed_enemy_ids

        self.crystals = []
        for i, pos in enumerate(data["crystals"]):
            cid = f"level{index}_crystal{i}"
            if cid not in collected_ids:
                self.crystals.append({"id": cid, "rect": pygame.Rect(pos[0], pos[1], 26, 36)})
        self.total_crystals = len(data["crystals"])

        self.hearts = []

        if "hearts" in data:
            herzen_liste = data["hearts"]
        else:
            herzen_liste = []

        for i, pos in enumerate(herzen_liste):
            self.hearts.append({"id": f"level{index}_heart{i}", "rect": pygame.Rect(pos[0], pos[1], 28, 28)})

        self.enemies = []
        for i, e in enumerate(data["enemies"]):
            eid = f"level{index}_enemy{i}"
            enemy = Enemy(eid, e[0], e[1], e[2], e[3], mini_enemy_sprites, hp=1, kind="mini")
            if eid in killed_enemy_ids:
                enemy.alive = False
            self.enemies.append(enemy)

    # KI Anfang
    # KI chatGPT
    # prompt: Bitte erstelle Funktionen zum Verwalten von Sammelobjekten sowie zeichnen des Levels mit Plattformen, Stacheln, Herzen, Kristallen, gegnern und portal erstellen

    @property
    def collected_count(self):
        return self.total_crystals - len(self.crystals)

    def get_collected_ids(self):
        existing = set()
        for c in self.crystals:
            existing.add(c["id"])

        gesammelte_liste = []
        for i in range(self.total_crystals):
            kristall_id = f"level{self.index}_crystal{i}"
            if kristall_id not in existing:
                gesammelte_liste.append(kristall_id)
        return gesammelte_liste

    def get_killed_enemy_ids(self):
        toten_liste = []
        for e in self.enemies:
            if not e.alive:
                toten_liste.append(e.id)
        return toten_liste

    def draw(self, surface, camera_x):
        if self.background:
            surface.blit(self.background, (0, 0))
        else:
            surface.fill((15, 15, 35))
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 88))
        surface.blit(overlay, (0, 0))

        for p in self.platforms:
            r = p.move(-camera_x, 0)
            pygame.draw.rect(surface, (58, 66, 96), r, border_radius=4)
            pygame.draw.rect(surface, (22, 28, 48), r, 3, border_radius=4)
            pygame.draw.rect(surface, (93, 106, 148), (r.x, r.y, r.width, 5), border_radius=3)
            step = 24
            for x in range(r.x + 10, r.x + r.width, step):
                pygame.draw.line(surface, (37, 44, 68), (x, r.y + 8), (x, r.bottom - 5), 2)
            for y in range(r.y + 14, r.bottom - 6, 10):
                pygame.draw.line(surface, (42, 48, 74), (r.x + 4, y), (r.right - 4, y), 1)

        for s in self.spikes:
            x, y = s.x - camera_x, s.y
            for i in range(0, s.width, 16):
                pts = [(x + i, y + 32), (x + i + 8, y + 6), (x + i + 16, y + 32)]
                pygame.draw.polygon(surface, (160, 165, 180), pts)
                pygame.draw.polygon(surface, (45, 45, 60), pts, 2)

        for c in self.crystals:
            r = c["rect"].move(-camera_x, 0)
            glow = pygame.Surface((44, 50), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (85, 255, 220, 70), (5, 8, 34, 34))
            surface.blit(glow, (r.x - 9, r.y - 8))
            pts = [(r.centerx, r.top), (r.right, r.y + 13), (r.centerx + 6, r.bottom), (r.left, r.y + 13)]
            pygame.draw.polygon(surface, (70, 245, 220), pts)
            pygame.draw.polygon(surface, (220, 255, 255), pts, 2)

        for heart in self.hearts:
            r = heart["rect"].move(-camera_x, 0)
            if self.heart_image:
                surface.blit(self.heart_image, (r.x, r.y))

        for e in self.enemies:
            e.draw(surface, camera_x)

        p = self.portal.move(-camera_x, 0)
        if self.portal_image:
            portal_rect = self.portal_image.get_rect(midbottom=(p.centerx, p.bottom))
            surface.blit(self.portal_image, portal_rect)
        else:
            pygame.draw.rect(surface, (55, 55, 75), p, border_radius=14)
            pygame.draw.rect(surface, (105, 95, 150), p, 4, border_radius=14)
        # KI Ende


def load_level_data(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))
