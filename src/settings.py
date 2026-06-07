from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
IMAGE_DIR = ASSETS_DIR / "images"
SOUND_DIR = ASSETS_DIR / "sounds"
SAVE_FILE = PROJECT_DIR / "savegame.json"
RANKING_FILE = PROJECT_DIR / "rankings.json"
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
FPS = 60
GRAVITY = 0.85
PLAYER_SPEED = 5.0
PLAYER_JUMP = -15.5
