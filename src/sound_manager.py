import pygame
from pathlib import Path


class SoundManager:
    def __init__(self, sound_dir: Path):
        self.sound_dir = sound_dir
        self.enabled = False
        self.sounds = {}
        # KI-Anfang
        # KI: ChatGPT
        # prompt: Robuste Pygame Soundverwaltung mit Hintergrundmusik erstellen.
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.enabled = True
        except pygame.error:
            self.enabled = False
        if self.enabled:
            for name in ["jump", "collect", "hit", "attack", "win", "damage", "level_complete"]:
                p = sound_dir / f"{name}.wav"
                try:
                    if p.exists():
                        self.sounds[name] = pygame.mixer.Sound(str(p))
                except (pygame.error, OSError):
                    pass
        # KI-Ende

    def play(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def start_music(self) -> None:
        if not self.enabled:
            return
        p = self.sound_dir / "background_music.wav"
        if not p.exists():
            return
        try:
            pygame.mixer.music.load(str(p))
            pygame.mixer.music.set_volume(0.22)
            pygame.mixer.music.play(-1)
        except (pygame.error, OSError):
            pass
