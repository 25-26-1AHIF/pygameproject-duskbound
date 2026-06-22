import pygame
from level import Level, load_level_data
from player import Player
from save_system import save_game, load_game, save_ranking, load_rankings
from settings import DATA_DIR, IMAGE_DIR, SAVE_FILE, RANKING_FILE, SOUND_DIR, WINDOW_HEIGHT, WINDOW_WIDTH, FPS
from sound_manager import SoundManager
from ui import draw_button, draw_center_text, draw_hud, make_font

class Game:
    def __init__(self, screen):
        self.window = screen
        self.screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT)).convert()
        self.fullscreen = False
        self.display_rect = pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.scale_factor = 1.0
        self.clock = pygame.time.Clock()
        self.small_font = make_font(24, True)
        self.medium_font = make_font(34, True)
        self.big_font = make_font(72, True)
        self.sounds = SoundManager(SOUND_DIR)
        self.sounds.start_music()
        self.level_data = load_level_data(DATA_DIR / "levels.json")
        self.images = self.load_images()

        self.state = "MENU"
        self.level_index = 0
        self.level = None
        self.player = None
        self.score = 0
        self.camera_x = 0

        self.player_name = ""
        self.name_input = ""
        self.start_ticks = 0
        self.final_time_seconds = 0
        self.ranking_saved = False
        self.rankings = load_rankings(RANKING_FILE)

        self.status_message = ""
        self.status_timer = 0
        self.next_level_index = 0
        self.level_complete_timer = 0
        self.completed_level_number = 0

        self.menu_buttons = {
            "start": pygame.Rect(WINDOW_WIDTH//2-150, 220, 300, 54),
            "load": pygame.Rect(WINDOW_WIDTH//2-150, 286, 300, 54),
            "rankings": pygame.Rect(WINDOW_WIDTH//2-150, 352, 300, 54),
            "controls": pygame.Rect(WINDOW_WIDTH//2-150, 418, 300, 54),
            "quit": pygame.Rect(WINDOW_WIDTH//2-150, 484, 300, 44),
        }
        self.controls_back_button = pygame.Rect(WINDOW_WIDTH//2-140, 455, 280, 54)


    def update_display_transform(self):
        window_width, window_height = self.window.get_size()
        scale = min(window_width / WINDOW_WIDTH, window_height / WINDOW_HEIGHT)
        scaled_width = int(WINDOW_WIDTH * scale)
        scaled_height = int(WINDOW_HEIGHT * scale)
        x = (window_width - scaled_width) // 2
        y = (window_height - scaled_height) // 2

        self.scale_factor = scale
        self.display_rect = pygame.Rect(x, y, scaled_width, scaled_height)

    def get_mouse_pos(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if not self.display_rect.collidepoint(mouse_x, mouse_y):
            return (-9999, -9999)

        logical_x = int((mouse_x - self.display_rect.x) / self.scale_factor)
        logical_y = int((mouse_y - self.display_rect.y) / self.scale_factor)
        return (logical_x, logical_y)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen

        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

        self.update_display_transform()

    def present(self):
        self.update_display_transform()
        self.window.fill((0, 0, 0))

        if self.display_rect.size == (WINDOW_WIDTH, WINDOW_HEIGHT):
            self.window.blit(self.screen, self.display_rect)
        else:
            scaled_surface = pygame.transform.scale(self.screen, self.display_rect.size)
            self.window.blit(scaled_surface, self.display_rect)

    def load_image(self, name, alpha=True):
        path = IMAGE_DIR / name
        try:
            return pygame.image.load(str(path)).convert_alpha() if alpha else pygame.image.load(str(path)).convert()
        except (pygame.error, FileNotFoundError, OSError):
            return None

    def load_frames(self, prefix):
        frames = []
        i = 0
        while True:
            img = self.load_image(f"{prefix}_{i}.png")
            if not img:
                break
            frames.append(img)
            i += 1
        return frames

    def load_images(self):
        return {
            "player": {
                "idle": self.load_frames("player_idle"),
                "run": self.load_frames("player_run"),
                "jump": self.load_frames("player_jump"),
                "attack": self.load_frames("player_attack"),
            },
            "mini_enemy": self.load_frames("enemy_mini_knight"),
            "boss_enemy": self.load_frames("enemy_dark_knight"),
            "heart": self.load_image("heart.png"),
            "portal": self.load_image("portal.png"),
            "backgrounds": {f"background_{i}.png": self.load_image(f"background_{i}.png", alpha=False) for i in range(1,6)}
        }

    def begin_name_input(self):
        self.name_input = self.player_name or ""
        self.state = "NAME_INPUT"

    def new_game(self):
        self.player_name = self.name_input.strip()[:18] or "Spieler"
        self.level_index = 0
        self.score = 0
        self.final_time_seconds = 0
        self.ranking_saved = False
        self.start_ticks = pygame.time.get_ticks()
        self.load_level(0)
        self.state = "PLAYING"

    def load_level(self, index, saved=None):
        collected = saved.get("collected_crystal_ids", []) if saved else []
        killed = saved.get("killed_enemy_ids", []) if saved else []
        self.level_index = index
        data = self.level_data[index]
        bg = self.images["backgrounds"].get(data.get("background"))
        self.level = Level(index, data, collected, killed, self.images["mini_enemy"], self.images["boss_enemy"], bg, self.images["heart"], self.images["portal"])
        self.player = Player(*self.level.spawn, self.images["player"])
        if saved:
            self.player.hp = saved.get("hp", self.player.max_hp)
            self.score = saved.get("score", self.score)
            self.player_name = saved.get("player_name", "Spieler")
            self.start_ticks = pygame.time.get_ticks() - int(saved.get("elapsed_seconds", 0) * 1000)
        self.camera_x = 0
        self.status_message = self.level.name
        self.status_timer = 110

    def elapsed_seconds(self):
        if self.start_ticks <= 0:
            return 0
        return max(0, (pygame.time.get_ticks() - self.start_ticks) // 1000)

    def save_current_game(self):
        if not self.level or not self.player:
            return
        save_game(SAVE_FILE, {
            "level_index": self.level_index,
            "hp": self.player.hp,
            "score": self.score,
            "player_name": self.player_name or "Spieler",
            "elapsed_seconds": self.elapsed_seconds(),
            "collected_crystal_ids": self.level.get_collected_ids(),
            "killed_enemy_ids": self.level.get_killed_enemy_ids()
        })
        self.status_message = "Spiel gespeichert!"
        self.status_timer = 80

    def load_saved_game(self):
        data = load_game(SAVE_FILE)
        if not data:
            self.status_message = "Kein Spielstand gefunden."
            self.status_timer = 90
            return False
        index = max(0, min(data.get("level_index", 0), len(self.level_data)-1))
        self.load_level(index, data)
        self.state = "PLAYING"
        return True

    def player_attack(self):
        if self.player:
            self.player.start_attack()
            self.sounds.play("attack")

    def finish_game(self):
        self.final_time_seconds = self.elapsed_seconds()
        if not self.ranking_saved:
            self.rankings = save_ranking(
                RANKING_FILE,
                self.player_name or "Spieler",
                self.score,
                self.final_time_seconds
            )
            self.ranking_saved = True
        self.state = "WIN"
        self.sounds.play("win")

    # KI-Anfang
    # KI: ChatGPT
    # prompt: Pygame-Hauptlogik mit Menü, Namenseingabe, Rankingliste, Schwertangriff, Gegnerangriff, Heart-Pickups und Levelwechsel erstellen.
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.state == "NAME_INPUT" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.new_game()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "MENU"
                elif event.key == pygame.K_BACKSPACE:
                    self.name_input = self.name_input[:-1]
                elif len(self.name_input) < 18 and event.unicode and event.unicode.isprintable():
                    self.name_input += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self.get_mouse_pos()
                if self.state == "MENU":
                    if self.menu_buttons["start"].collidepoint(pos):
                        self.begin_name_input()
                    elif self.menu_buttons["load"].collidepoint(pos):
                        self.load_saved_game()
                    elif self.menu_buttons["rankings"].collidepoint(pos):
                        self.rankings = load_rankings(RANKING_FILE)
                        self.state = "RANKINGS"
                    elif self.menu_buttons["controls"].collidepoint(pos):
                        self.state = "CONTROLS"
                    elif self.menu_buttons["quit"].collidepoint(pos):
                        return False
                elif self.state in ("CONTROLS", "RANKINGS"):
                    if self.controls_back_button.collidepoint(pos):
                        self.state = "MENU"
                elif self.state == "PLAYING":
                    self.player_attack()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                    continue

                if self.state == "MENU":
                    if event.key == pygame.K_RETURN:
                        self.begin_name_input()
                    elif event.key == pygame.K_l:
                        self.load_saved_game()
                    elif event.key == pygame.K_ESCAPE:
                        return False
                elif self.state in ("CONTROLS", "RANKINGS"):
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        self.state = "MENU"
                elif self.state == "PLAYING":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "PAUSED"
                    elif event.key in (pygame.K_w, pygame.K_UP) and self.player:
                        self.player.jump()
                    elif event.key == pygame.K_SPACE:
                        self.player_attack()
                    elif event.key == pygame.K_F5:
                        self.save_current_game()
                elif self.state == "PAUSED":
                    if event.key == pygame.K_RETURN:
                        self.state = "PLAYING"
                    elif event.key == pygame.K_F5:
                        self.save_current_game()
                    elif event.key == pygame.K_m:
                        self.state = "MENU"
                elif self.state in ("GAME_OVER", "WIN"):
                    if event.key == pygame.K_RETURN:
                        self.begin_name_input()
                    elif event.key == pygame.K_m:
                        self.state = "MENU"
        return True

    def update_playing(self):
        if not self.level or not self.player:
            return

        keys = pygame.key.get_pressed()
        if self.player.update(keys, self.level.platforms):
            self.sounds.play("jump")

        if self.player.rect.top > WINDOW_HEIGHT + 100:
            self.player.hp = 0

        for s in self.level.spikes:
            if self.player.rect.colliderect(s):
                direction = 1 if self.player.rect.centerx < s.centerx else -1
                if self.player.take_damage(direction):
                    self.sounds.play("damage")

        if self.player.attack_timer > 0 and not self.player.attack_hit_done:
            attack_rect = self.player.attack_rect()
            for e in self.level.enemies:
                if e.alive and attack_rect.colliderect(e.rect):
                    killed = e.take_hit(1)
                    self.player.attack_hit_done = True
                    self.sounds.play("hit")
                    if killed:
                        self.score += 100
                    break

        for e in self.level.enemies:
            e.update(self.player.rect)
            if e.attack_timer > 0 and not e.attack_hit_done and e.attack_rect().colliderect(self.player.rect):
                direction = 1 if self.player.rect.centerx < e.rect.centerx else -1
                if self.player.take_damage(direction):
                    self.sounds.play("damage")
                e.attack_hit_done = True
            # Kein Kontaktschaden mehr. Schaden entsteht nur durch den sichtbaren Schwertangriff.

        for c in self.level.crystals[:]:
            if self.player.rect.colliderect(c["rect"]):
                self.level.crystals.remove(c)
                self.score += 50
                self.sounds.play("collect")

        for h in self.level.hearts[:]:
            if self.player.rect.colliderect(h["rect"]):
                self.level.hearts.remove(h)
                self.player.hp = min(self.player.max_hp, self.player.hp + 1)
                self.score += 25
                self.status_message = "Herz eingesammelt!"
                self.status_timer = 55
                self.sounds.play("collect")

        if self.player.rect.colliderect(self.level.portal):
            if self.level.collected_count >= self.level.total_crystals:
                if self.level_index + 1 >= len(self.level_data):
                    self.finish_game()
                else:
                    self.score += 250
                    self.completed_level_number = self.level_index + 1
                    self.next_level_index = self.level_index + 1
                    self.level_complete_timer = 125
                    self.state = "LEVEL_COMPLETE"
                    self.sounds.play("level_complete")
            else:
                self.status_message = "Sammle zuerst alle Kristalle!"
                self.status_timer = 70

        if self.player.hp <= 0:
            self.state = "GAME_OVER"

        self.camera_x = max(0, min(self.player.rect.centerx - WINDOW_WIDTH//2, self.level.width - WINDOW_WIDTH))
        if self.status_timer > 0:
            self.status_timer -= 1
    # KI-Ende

    def update_level_complete(self):
        if self.level_complete_timer > 0:
            self.level_complete_timer -= 1
        else:
            self.load_level(self.next_level_index)
            self.state = "PLAYING"

    def update(self):
        if self.state == "PLAYING":
            self.update_playing()
        elif self.state == "LEVEL_COMPLETE":
            self.update_level_complete()

    def draw_menu_bg(self):
        bg = self.images["backgrounds"].get("background_3.png") or next(iter(self.images["backgrounds"].values()))
        if bg:
            self.screen.blit(bg, (0,0))
        else:
            self.screen.fill((15,15,35))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,125))
        self.screen.blit(overlay,(0,0))

    def draw_menu(self):
        self.draw_menu_bg()
        pos = self.get_mouse_pos()
        draw_center_text(self.screen, "DUSKBOUND", self.big_font, 55)
        draw_center_text(self.screen, "", self.medium_font, 135, (225,210,255))
        draw_button(self.screen, self.menu_buttons["start"], "Neues Spiel", self.medium_font, pos)
        draw_button(self.screen, self.menu_buttons["load"], "Spiel laden", self.medium_font, pos)
        draw_button(self.screen, self.menu_buttons["rankings"], "Highscores", self.medium_font, pos)
        draw_button(self.screen, self.menu_buttons["controls"], "Steuerung", self.medium_font, pos)
        draw_button(self.screen, self.menu_buttons["quit"], "Beenden", self.medium_font, pos)
        if self.status_timer > 0:
            draw_center_text(self.screen, self.status_message, self.small_font, 510, (255,220,120))
            self.status_timer -= 1

    def draw_name_input(self):
        self.draw_menu_bg()
        draw_center_text(self.screen, "NAME EINGEBEN", self.big_font, 95)
        draw_center_text(self.screen, "Tippe deinen Namen und drücke ENTER", self.medium_font, 185, (225,210,255))
        box = pygame.Rect(WINDOW_WIDTH//2 - 230, 270, 460, 70)
        pygame.draw.rect(self.screen, (18, 14, 34), box, border_radius=14)
        pygame.draw.rect(self.screen, (150, 110, 220), box, 3, border_radius=14)
        shown = self.name_input if self.name_input else "Spieler"
        label = self.medium_font.render(shown, True, (255,255,255))
        self.screen.blit(label, (box.centerx - label.get_width()//2, box.centery - label.get_height()//2))
        draw_center_text(self.screen, "ESC = zurück", self.small_font, 390, (230,230,230))

    def draw_controls(self):
        self.draw_menu_bg()
        pos = self.get_mouse_pos()
        draw_center_text(self.screen, "STEUERUNG", self.big_font, 48)
        panel = pygame.Rect(95,135,770,285)
        pygame.draw.rect(self.screen, (14,11,28), panel, border_radius=18)
        pygame.draw.rect(self.screen, (130,95,205), panel, 3, border_radius=18)
        key_font, desc_font = make_font(25, True), make_font(22)
        controls = [("A / D","Nach links und rechts bewegen"),("W","Springen und Doppelsprung"),("SPACE","Schwertangriff"),("Linksklick","Schwertangriff"),("ESC","Pause-Menü öffnen"),("F5","Spielstand speichern")]
        y = 160
        for key, desc in controls:
            box = pygame.Rect(130,y-4,170,32)
            pygame.draw.rect(self.screen, (35,26,62), box, border_radius=8)
            pygame.draw.rect(self.screen, (115,85,180), box, 2, border_radius=8)
            ki, di = key_font.render(key, True, (255,255,255)), desc_font.render(desc, True, (225,220,240))
            self.screen.blit(ki, (box.centerx-ki.get_width()//2, box.centery-ki.get_height()//2))
            self.screen.blit(di, (330,y))
            y += 40
        draw_button(self.screen, self.controls_back_button, "Zurück", self.medium_font, pos)

    def draw_rankings(self):
        self.draw_menu_bg()
        pos = self.get_mouse_pos()
        draw_center_text(self.screen, "HIGHSCORES", self.big_font, 45)
        panel = pygame.Rect(160, 130, 640, 300)
        pygame.draw.rect(self.screen, (14, 11, 28), panel, border_radius=18)
        pygame.draw.rect(self.screen, (130, 95, 205), panel, 3, border_radius=18)
        font = make_font(24, True)
        if not self.rankings:
            draw_center_text(self.screen, "Noch keine Einträge", self.medium_font, 250)
        else:
            y = 155
            for i, entry in enumerate(self.rankings[:10], start=1):
                minutes = entry["time_seconds"] // 60
                seconds = entry["time_seconds"] % 60
                text = f"{i}. {entry['name']}   Score: {entry['score']}   Zeit: {minutes:02d}:{seconds:02d}"
                img = font.render(text, True, (235, 230, 250))
                self.screen.blit(img, (190, y))
                y += 26
        draw_button(self.screen, self.controls_back_button, "Zurück", self.medium_font, pos)

    def draw_playing(self):
        if not self.level or not self.player:
            return
        self.level.draw(self.screen, self.camera_x)
        self.player.draw(self.screen, self.camera_x)
        draw_hud(self.screen, self.player.hp, self.level_index+1, self.level.collected_count, self.level.total_crystals, self.score, self.images["heart"])
        time_string = f"Zeit: {self.elapsed_seconds() // 60:02d}:{self.elapsed_seconds() % 60:02d}"

        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            shadow = self.small_font.render(time_string, True, (0, 0, 0))
            self.screen.blit(shadow, (790 + ox, 78 + oy))

        time_text = self.small_font.render(time_string, True, (240, 240, 240))
        self.screen.blit(time_text, (790, 78))
        if self.status_timer > 0:
            draw_center_text(self.screen, self.status_message, self.small_font, 110, (255,230,130))

    def draw_pause(self):
        self.draw_playing()
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,165))
        self.screen.blit(overlay,(0,0))
        draw_center_text(self.screen, "PAUSE", self.big_font, 130)
        draw_center_text(self.screen, "ENTER = Weiter", self.medium_font, 245)
        draw_center_text(self.screen, "F5 = Speichern", self.medium_font, 295)
        draw_center_text(self.screen, "M = Hauptmenü", self.medium_font, 345)

    def draw_level_complete(self):
        self.draw_menu_bg()
        draw_center_text(self.screen, f"LEVEL {self.completed_level_number} GEMEISTERT!", self.big_font, 145)
        draw_center_text(self.screen, "Nächstes Level wird geladen ...", self.medium_font, 280, (230,220,255))

    def draw_game_over(self):
        self.screen.fill((32,8,18))
        draw_center_text(self.screen, "GAME OVER", self.big_font, 115)
        draw_center_text(self.screen, f"Score: {self.score}", self.medium_font, 220)
        draw_center_text(self.screen, "ENTER = Neustart", self.medium_font, 310)
        draw_center_text(self.screen, "M = Hauptmenü", self.medium_font, 360)

    def draw_win(self):
        self.draw_menu_bg()
        draw_center_text(self.screen, "GEWONNEN!", self.big_font, 45)
        draw_center_text(self.screen, f"{self.player_name} - Score: {self.score} - Zeit: {self.final_time_seconds//60:02d}:{self.final_time_seconds%60:02d}", self.medium_font, 130)
        panel = pygame.Rect(160, 190, 640, 220)
        pygame.draw.rect(self.screen, (14, 11, 28), panel, border_radius=18)
        pygame.draw.rect(self.screen, (130, 95, 205), panel, 3, border_radius=18)
        font = make_font(23, True)
        y = 215
        for i, entry in enumerate(self.rankings[:7], start=1):
            minutes = entry["time_seconds"] // 60
            seconds = entry["time_seconds"] % 60
            text = f"{i}. {entry['name']}   Score: {entry['score']}   Zeit: {minutes:02d}:{seconds:02d}"
            img = font.render(text, True, (235, 230, 250))
            self.screen.blit(img, (190, y))
            y += 28
        draw_center_text(self.screen, "ENTER = nochmal spielen | M = Hauptmenü", self.small_font, 450)

    def draw(self):
        if self.state == "MENU": self.draw_menu()
        elif self.state == "NAME_INPUT": self.draw_name_input()
        elif self.state == "CONTROLS": self.draw_controls()
        elif self.state == "RANKINGS": self.draw_rankings()
        elif self.state == "PLAYING": self.draw_playing()
        elif self.state == "PAUSED": self.draw_pause()
        elif self.state == "LEVEL_COMPLETE": self.draw_level_complete()
        elif self.state == "GAME_OVER": self.draw_game_over()
        elif self.state == "WIN": self.draw_win()

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            running = self.handle_events()
            self.update()
            self.draw()
            self.present()
            pygame.display.flip()
