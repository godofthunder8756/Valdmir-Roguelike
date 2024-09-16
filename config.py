# config.py

import pygame

# Game Settings
WINDOW_WIDTH = 1280  # Increased from 800
WINDOW_HEIGHT = 720  # Increased from 600
FPS = 60  # Frames per second

# Time Settings
TIME_INCREMENT = 10  # Minutes per turn
DAY_START = 6 * 60  # 6:00 AM in minutes
NIGHT_START = 19 * 60  # 7:00 PM in minutes
INITIAL_TIME = 12 * 60  # 12:00 PM in minutes

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PANEL_BG = (50, 50, 50)
PANEL_TEXT = (200, 200, 200)
YELLOW = (255, 255, 0)
LIGHT_GREEN = (144, 238, 144)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_GRAY = (50, 50, 50)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
BROWN = (139, 69, 19)
GRAY = (169, 169, 169)

# Fonts
FONT_SIZE = 16
FONT_NAME = 'couriernew'  # Use a monospaced font

# Grid settings
TILE_SIZE = 16
LOCAL_MAP_WIDTH = 100  # Width of local map (in tiles)
LOCAL_MAP_HEIGHT = 100  # Height of local map (in tiles)
VIEWPORT_WIDTH = (WINDOW_WIDTH - 200) // TILE_SIZE  # Visible tiles in viewport
VIEWPORT_HEIGHT = WINDOW_HEIGHT // TILE_SIZE

# World Map settings (Increased size)
WORLD_MAP_WIDTH = 40  # Increased from 20
WORLD_MAP_HEIGHT = 30  # Increased from 15
CELL_SIZE = 32  # Size of each cell on the world map display

# Biome and terrain tiles
TILES = {
    'PLAIN': {'char': '.', 'color': (34, 139, 34), 'walkable': True, 'name': 'Plains'},
    'FOREST': {'char': 'T', 'color': (0, 100, 0), 'walkable': False, 'name': 'Forest'},
    'MOUNTAIN': {'char': '^', 'color': (139, 137, 137), 'walkable': False, 'name': 'Mountain'},
    'DESERT': {'char': '.', 'color': (237, 201, 175), 'walkable': True, 'name': 'Desert'},
    'WATER': {'char': '~', 'color': (0, 105, 148), 'walkable': False, 'name': 'Water'},
    'HOUSE_WALL': {'char': '#', 'color': (150, 75, 0), 'walkable': False, 'name': 'Wall'},
    'HOUSE_FLOOR': {'char': '.', 'color': (210, 180, 140), 'walkable': True, 'name': 'Floor'},
    'DOOR': {'char': '+', 'color': YELLOW, 'walkable': True, 'name': 'Door'},
    'DUNGEON_ENTRANCE': {'char': '+', 'color': GRAY, 'walkable': True, 'name': 'Dungeon Entrance'},
    'FLOOR': {'char': '.', 'color': (150, 150, 150), 'walkable': True, 'name': 'Floor'},
    'WALL': {'char': '#', 'color': (100, 100, 100), 'walkable': False, 'name': 'Wall'},
    'STAIRS_DOWN': {'char': '\u25BC', 'color': GREEN, 'walkable': True, 'name': 'Stairs Down'},
    'CHEST': {'char': 'C', 'color': YELLOW, 'walkable': True, 'name': 'Chest'},
}

BIOMES = ['PLAIN', 'FOREST', 'MOUNTAIN', 'DESERT', 'WATER']
BIOME_COLORS = {
    'PLAIN': (34, 139, 34),
    'FOREST': (0, 100, 0),
    'MOUNTAIN': (139, 137, 137),
    'DESERT': (237, 201, 175),
    'WATER': (0, 105, 148),
    'TOWN': YELLOW,  # Color for towns on the world map
}

# Enemy Stats
ENEMY_STATS = {
    'Goblin': {
        'char': 'G',
        'color': LIGHT_GREEN,
        'attack': (5, 10),
        'health': 20,
        'xp': 10,
        'gold': (1, 5),
        'behavior': 'aggressive',
    },
    'Snake': {
        'char': 's',
        'color': RED,
        'attack': (8, 15),
        'health': 15,
        'xp': 15,
        'gold': (0, 3),
        'behavior': 'random',
    },
    'Bandit': {
        'char': 'b',
        'color': GRAY,
        'attack': (10, 20),
        'health': 25,
        'xp': 20,
        'gold': (5, 15),
        'behavior': 'aggressive',
    },
    'Bat': {
        'char': 'm',
        'color': PURPLE,
        'attack': (3, 7),
        'health': 10,
        'xp': 5,
        'gold': (0, 2),
        'behavior': 'aggressive',
    },
}

# Villager Stats
VILLAGER_STATS = {
    'char': '@',
    'color': BROWN,
}

# Item List
ITEMS = ['Health Potion', 'Sword', 'Shield', 'Magic Ring']

# Prices for Items
ITEM_PRICES = {
    'Health Potion': 10,
    'Sword': 50,
    'Shield': 40,
    'Magic Ring': 100,
}

class Rect:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center_x(self):
        return (self.x1 + self.x2) // 2

    def center_y(self):
        return (self.y1 + self.y2) // 2

    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)
    
# Helper function for drawing text
def draw_text(surface, text, x, y, color=WHITE, font_size=FONT_SIZE, font_name=FONT_NAME):
    font = pygame.font.SysFont(font_name, font_size)
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))