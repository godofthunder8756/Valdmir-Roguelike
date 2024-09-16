# roguelike_pygame_worldmap_updated.py

import pygame
import sys
import random
import time
import textwrap
from config import *

class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        stats = ENEMY_STATS[enemy_type]
        self.char = stats['char']
        self.color = stats['color']
        self.name = enemy_type
        self.attack = random.randint(*stats['attack'])
        self.health = stats['health']
        self.max_health = stats['health']
        self.xp = stats['xp']
        self.gold = random.randint(*stats['gold'])
        self.behavior = stats['behavior']

    def move(self, player_x, player_y, local_map, time_of_day):
        if self.behavior == 'aggressive':
            # Simple line-of-sight check (Manhattan distance)
            distance = abs(self.x - player_x) + abs(self.y - player_y)
            if distance <= 10:
                dx = player_x - self.x
                dy = player_y - self.y
                if abs(dx) > abs(dy):
                    step_x = 1 if dx > 0 else -1
                    if TILES[local_map[self.y][self.x + step_x]]['walkable']:
                        self.x += step_x
                else:
                    step_y = 1 if dy > 0 else -1
                    if TILES[local_map[self.y + step_y][self.x]]['walkable']:
                        self.y += step_y
        elif self.behavior == 'random':
            # Move randomly
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            new_x = self.x + dx
            new_y = self.y + dy
            if 0 <= new_x < LOCAL_MAP_WIDTH and 0 <= new_y < LOCAL_MAP_HEIGHT:
                if TILES[local_map[new_y][new_x]]['walkable']:
                    self.x = new_x
                    self.y = new_y

class Villager:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.char = VILLAGER_STATS['char']
        self.color = VILLAGER_STATS['color']
        self.name = 'Villager'

    def move(self, local_map):
        # Simple random walk within town area
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        new_x = self.x + dx
        new_y = self.y + dy
        if 0 <= new_x < LOCAL_MAP_WIDTH and 0 <= new_y < LOCAL_MAP_HEIGHT:
            if TILES[local_map[new_y][new_x]]['walkable']:
                self.x = new_x
                self.y = new_y

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Valdmir')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
        self.running = True

        # Game state
        self.state = 'main_menu'

        # Player variables
        self.player_char = '@'
        self.player_color = WHITE
        self.player_x = 0
        self.player_y = 0
        self.level = 1
        self.attack = 5
        self.xp = 0
        self.gold = 0
        self.inventory = []
        self.equipped_items = []

        # Current cell position in world map
        self.current_cell = (WORLD_MAP_WIDTH // 2, WORLD_MAP_HEIGHT // 2)
        self.selected_cell = self.current_cell

        # Game variables
        self.health = 100
        self.max_health = 100
        self.events = []
        self.message = ''

        # Time variables
        self.time = INITIAL_TIME

        # World map
        self.world_map = self.generate_world_map()

        # Local maps for each world cell
        self.world_cells = {}  # Key: (cell_x, cell_y), Value: {'local_map', 'player_x', 'player_y', 'enemies', 'villagers'}

        # Map stack to handle multiple map levels
        self.map_stack = []

        # Enemies
        self.enemies = []

        # Villagers
        self.villagers = []

        # Combat variables
        self.in_combat = False
        self.current_enemy = None

        # Command mode
        self.command_mode = False
        self.command_input = ''

        # HUD visibility
        self.hud_visible = True  # New variable to track HUD visibility

    def generate_world_map(self):
        world_map = [[{'biome': 'PLAIN', 'town': False, 'dungeons': [], 'name': None} for _ in range(WORLD_MAP_WIDTH)] for _ in range(WORLD_MAP_HEIGHT)]

        # Scatter blobs of other biomes
        num_blobs = 60  # Increased number for larger map
        for _ in range(num_blobs):
            biome = random.choice(['FOREST', 'MOUNTAIN', 'DESERT', 'WATER'])
            blob_size = random.randint(2, 5)
            blob_x = random.randint(0, WORLD_MAP_WIDTH - 1)
            blob_y = random.randint(0, WORLD_MAP_HEIGHT - 1)
            self.create_biome_blob(world_map, blob_x, blob_y, blob_size, biome)

        # Place towns/villages
        num_towns = 20  # Increased number of towns
        for _ in range(num_towns):
            town_x = random.randint(0, WORLD_MAP_WIDTH - 1)
            town_y = random.randint(0, WORLD_MAP_HEIGHT - 1)
            world_map[town_y][town_x]['town'] = True

        # Place dungeons
        for y in range(WORLD_MAP_HEIGHT):
            for x in range(WORLD_MAP_WIDTH):
                if random.random() < 0.5:
                    num_dungeons = random.randint(1, 3)
                    dungeon_positions = []
                    for _ in range(num_dungeons):
                        dungeon_positions.append(self.random_dungeon_position())
                    world_map[y][x]['dungeons'] = dungeon_positions

        return world_map

    def random_dungeon_position(self):
        # Return a random position within the local map bounds
        x = random.randint(5, LOCAL_MAP_WIDTH - 6)  # Avoid edges
        y = random.randint(5, LOCAL_MAP_HEIGHT - 6)
        return (x, y)

    def create_biome_blob(self, world_map, x, y, size, biome):
        cells_to_fill = [(x, y)]
        for _ in range(size):
            if cells_to_fill:
                cx, cy = cells_to_fill.pop(0)
                if 0 <= cx < WORLD_MAP_WIDTH and 0 <= cy < WORLD_MAP_HEIGHT:
                    world_map[cy][cx]['biome'] = biome
                    # Add neighboring cells
                    neighbors = [
                        (cx + 1, cy), (cx - 1, cy),
                        (cx, cy + 1), (cx, cy - 1)
                    ]
                    random.shuffle(neighbors)
                    cells_to_fill.extend(neighbors[:2])

    def generate_local_map(self, cell_x, cell_y, entrance_direction=None):
        cell_key = (cell_x, cell_y)
        if cell_key in self.world_cells:
            # Load existing local map and state
            cell_data = self.world_cells[cell_key]
            self.local_map = cell_data['local_map']
            self.player_x = cell_data['player_x']
            self.player_y = cell_data['player_y']
            self.enemies = cell_data['enemies']
            self.villagers = cell_data['villagers']
            self.local_map_biome = cell_data['biome']
            return self.local_map
        else:
            # Generate new local map
            # Get the biome of the selected cell
            cell_data = self.world_map[cell_y][cell_x]
            biome = cell_data['biome']
            self.local_map_biome = biome

            # Initialize the local map here
            self.local_map = [[None for _ in range(LOCAL_MAP_WIDTH)] for _ in range(LOCAL_MAP_HEIGHT)]

            # Generate the local map based on the biome
            for y in range(LOCAL_MAP_HEIGHT):
                for x in range(LOCAL_MAP_WIDTH):
                    tile = self.generate_tile(biome)
                    self.local_map[y][x] = tile

            # Optionally, add features based on whether the cell contains a town
            if cell_data['town']:
                self.place_town(self.local_map)

            # Place dungeon entrances if any
            for dungeon_pos in cell_data.get('dungeons', []):
                x, y = dungeon_pos
                self.local_map[y][x] = 'DUNGEON_ENTRANCE'

            # Set player's position based on entrance direction
            if entrance_direction is None:
                # Initial spawn, set to center
                self.player_x = LOCAL_MAP_WIDTH // 2
                self.player_y = LOCAL_MAP_HEIGHT // 2
            else:
                # Set player's position based on entrance direction
                if entrance_direction == 'left':
                    self.player_x = 0  # Entering from left
                    self.player_y = LOCAL_MAP_HEIGHT // 2
                elif entrance_direction == 'right':
                    self.player_x = LOCAL_MAP_WIDTH - 1  # Entering from right
                    self.player_y = LOCAL_MAP_HEIGHT // 2
                elif entrance_direction == 'up':
                    self.player_x = LOCAL_MAP_WIDTH // 2
                    self.player_y = 0  # Entering from top
                elif entrance_direction == 'down':
                    self.player_x = LOCAL_MAP_WIDTH // 2
                    self.player_y = LOCAL_MAP_HEIGHT - 1  # Entering from bottom
                else:
                    # Default to center
                    self.player_x = LOCAL_MAP_WIDTH // 2
                    self.player_y = LOCAL_MAP_HEIGHT // 2

            # Ensure player's starting position is walkable
            attempts = 0
            max_attempts = LOCAL_MAP_WIDTH * LOCAL_MAP_HEIGHT
            while True:
                tile = self.local_map[self.player_y][self.player_x]
                if TILES[tile]['walkable']:
                    break
                else:
                    # Adjust position if not walkable
                    if entrance_direction == 'left':
                        self.player_x += 1
                    elif entrance_direction == 'right':
                        self.player_x -= 1
                    elif entrance_direction == 'up':
                        self.player_y += 1
                    elif entrance_direction == 'down':
                        self.player_y -= 1
                    else:
                        # Random position
                        self.player_x = random.randint(0, LOCAL_MAP_WIDTH - 1)
                        self.player_y = random.randint(0, LOCAL_MAP_HEIGHT - 1)
                    attempts += 1
                    if attempts > max_attempts:
                        # No walkable tile found
                        raise Exception('No walkable tile found for player to start')

            # Initialize enemies and villagers
            self.enemies = []
            self.villagers = []

            # Determine time of day
            time_of_day = self.get_time_of_day()

            if cell_data['town']:
                # Spawn villagers during the day
                if time_of_day == 'day':
                    self.spawn_villagers(self.local_map)
            else:
                self.spawn_enemies(self.local_map, time_of_day)

            # Save the new cell's state
            self.world_cells[cell_key] = {
                'local_map': self.local_map,
                'player_x': self.player_x,
                'player_y': self.player_y,
                'enemies': self.enemies,
                'villagers': self.villagers,
                'biome': self.local_map_biome,
            }
            return self.local_map


    def spawn_villagers(self, local_map):
        num_villagers = random.randint(3, 6)
        for _ in range(num_villagers):
            while True:
                x = random.randint(0, LOCAL_MAP_WIDTH - 1)
                y = random.randint(0, LOCAL_MAP_HEIGHT - 1)
                tile_type = local_map[y][x]
                tile = TILES.get(tile_type, TILES['PLAIN'])
                if tile['walkable'] and (x != self.player_x or y != self.player_y):
                    self.villagers.append(Villager(x, y))
                    break

    def spawn_enemies(self, local_map, time_of_day):
        num_enemies = random.randint(3, 6)
        enemy_types = ['Goblin', 'Snake', 'Bandit']
        if time_of_day == 'night':
            enemy_types.append('Bat')
        for _ in range(num_enemies):
            enemy_type = random.choice(enemy_types)
            while True:
                x = random.randint(0, LOCAL_MAP_WIDTH - 1)
                y = random.randint(0, LOCAL_MAP_HEIGHT - 1)
                tile_type = local_map[y][x]
                tile = TILES.get(tile_type, TILES['PLAIN'])
                if tile['walkable'] and (x != self.player_x or y != self.player_y):
                    self.enemies.append(Enemy(x, y, enemy_type))
                    break

    def place_town(self, local_map):
        # Place a town in the local map
        town_center_x = LOCAL_MAP_WIDTH // 2
        town_center_y = LOCAL_MAP_HEIGHT // 2
        town_size = 20  # Adjust the size of the town
        num_buildings = 5  # Number of buildings
        building_size = 6  # Size of each building

        # Clear the town area to plains
        for y in range(town_center_y - town_size // 2, town_center_y + town_size // 2):
            for x in range(town_center_x - town_size // 2, town_center_x + town_size // 2):
                if 0 <= x < LOCAL_MAP_WIDTH and 0 <= y < LOCAL_MAP_HEIGHT:
                    local_map[y][x] = 'PLAIN'  # Walkable area

        # Place buildings
        for i in range(num_buildings):
            # Randomly position buildings within the town area
            b_x = random.randint(town_center_x - town_size // 2, town_center_x + town_size // 2 - building_size)
            b_y = random.randint(town_center_y - town_size // 2, town_center_y + town_size // 2 - building_size)
            # Build building
            for y in range(b_y, b_y + building_size):
                for x in range(b_x, b_x + building_size):
                    if 0 <= x < LOCAL_MAP_WIDTH and 0 <= y < LOCAL_MAP_HEIGHT:
                        # Walls on the edges
                        if y == b_y or y == b_y + building_size -1 or x == b_x or x == b_x + building_size -1:
                            local_map[y][x] = 'HOUSE_WALL'
                        else:
                            local_map[y][x] = 'HOUSE_FLOOR'
            # Place door
            door_side = random.choice(['top', 'bottom', 'left', 'right'])
            if door_side == 'top':
                door_x = random.randint(b_x + 1, b_x + building_size - 2)
                door_y = b_y
            elif door_side == 'bottom':
                door_x = random.randint(b_x + 1, b_x + building_size - 2)
                door_y = b_y + building_size -1
            elif door_side == 'left':
                door_x = b_x
                door_y = random.randint(b_y + 1, b_y + building_size - 2)
            elif door_side == 'right':
                door_x = b_x + building_size -1
                door_y = random.randint(b_y + 1, b_y + building_size - 2)
            local_map[door_y][door_x] = 'DOOR'
        self.events.append('You have entered a town.')

    def generate_tile(self, biome):
        # Based on the biome, decide what tiles to generate
        if biome == 'PLAIN':
            # Mostly plains, with a chance for small features
            chance = random.random()
            if chance < 0.05:
                return 'FOREST'
            elif chance < 0.06:
                return 'MOUNTAIN'
            else:
                return 'PLAIN'
        elif biome == 'FOREST':
            # Mostly forest
            chance = random.random()
            if chance < 0.7:
                return 'FOREST'
            else:
                return 'PLAIN'
        elif biome == 'MOUNTAIN':
            # Mostly mountains
            chance = random.random()
            if chance < 0.7:
                return 'MOUNTAIN'
            else:
                return 'PLAIN'
        elif biome == 'DESERT':
            # Mostly desert
            chance = random.random()
            if chance < 0.1:
                return 'MOUNTAIN'
            else:
                return 'DESERT'
        elif biome == 'WATER':
            # Mostly water
            chance = random.random()
            if chance < 0.9:
                return 'WATER'
            else:
                return 'PLAIN'
        else:
            return 'PLAIN'

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            if self.state != 'combat':
                self.update_time()
            self.draw()
        pygame.quit()
        sys.exit()

    def update_time(self):
        # Increment time by TIME_INCREMENT minutes per turn
        self.time = (self.time + TIME_INCREMENT) % (24 * 60)  # Wrap around after 24 hours

    def get_time_of_day(self):
        if DAY_START <= self.time < NIGHT_START:
            return 'day'
        else:
            return 'night'

    def handle_events(self):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if self.state == 'main_menu':
                    self.state = 'world_map'  # Start the game
                elif self.command_mode:
                    self.handle_command_input(event)
                else:
                    if event.key == pygame.K_q:
                        self.running = False
                    if event.key == pygame.K_c:
                        self.command_mode = True
                        self.command_input = ''
                    if event.key == pygame.K_m:
                        # Toggle Map Mode
                        if self.state == 'local_map':
                            self.state = 'map_mode'
                        elif self.state == 'map_mode':
                            self.state = 'local_map'

                    if self.state in ('world_map', 'map_mode'):
                        self.handle_world_map_events(event)
                    elif self.state in ('local_map', 'dungeon'):
                        self.handle_local_map_events(event, keys)

    
    def handle_command_input(self, event):
        if event.key == pygame.K_RETURN:
            # Process command
            self.process_command(self.command_input.strip())
            self.command_mode = False
        elif event.key == pygame.K_BACKSPACE:
            self.command_input = self.command_input[:-1]
        else:
            self.command_input += event.unicode

    def process_command(self, command):
        command = command.lower()
        if command == 'time':
            current_hour = int(self.time // 60)
            current_minute = int(self.time % 60)
            time_str = f'{current_hour:02d}:{current_minute:02d}'
            self.events.append(f'Current time: {time_str}')
        elif command == 'fullscreen':
            pygame.display.toggle_fullscreen()
            self.events.append('Toggled fullscreen mode.')
        elif command == 'hud':
            self.hud_visible = not self.hud_visible
            state = 'shown' if self.hud_visible else 'hidden'
            self.events.append(f'HUD is now {state}.')
        elif command == 'regioninfo':
            self.display_region_info()
        else:
            self.events.append(f'Unknown command: {command}')

    def display_region_info(self):
        cell_x, cell_y = self.current_cell
        cell_data = self.world_map[cell_y][cell_x]
        biome = cell_data.get('biome', 'Unknown')
        has_town = cell_data.get('town', False)
        dungeons = cell_data.get('dungeons', [])
        has_dungeon = len(dungeons) > 0
        region_name = cell_data.get('name', 'Unknown')  # Name is null for now

        info_lines = [
            f"Region Info:",
            f" Biome: {biome}",
            f" Has Town: {'Yes' if has_town else 'No'}",
            f" Has Dungeon: {'Yes' if has_dungeon else 'No'}",
            f" Name: {region_name}",
        ]
        for line in info_lines:
            self.events.append(line)


    def handle_world_map_events(self, event):
        if event.key == pygame.K_RETURN and self.state == 'world_map':
            # Player selects the cell to spawn at
            cell_x, cell_y = self.selected_cell
            cell_data = self.world_map[cell_y][cell_x]
            if cell_data['biome'] == 'WATER':
                self.events.append('Cannot spawn in water. Please select another cell.')
            else:
                self.local_map = self.generate_local_map(cell_x, cell_y)
                self.current_cell = self.selected_cell
                self.state = 'local_map'
                self.events.append(f'Spawned in {self.local_map_biome}')
        elif event.key == pygame.K_w and self.selected_cell[1] > 0:
            self.selected_cell = (self.selected_cell[0], self.selected_cell[1] - 1)
        elif event.key == pygame.K_s and self.selected_cell[1] < WORLD_MAP_HEIGHT - 1:
            self.selected_cell = (self.selected_cell[0], self.selected_cell[1] + 1)
        elif event.key == pygame.K_a and self.selected_cell[0] > 0:
            self.selected_cell = (self.selected_cell[0] - 1, self.selected_cell[1])
        elif event.key == pygame.K_d and self.selected_cell[0] < WORLD_MAP_WIDTH - 1:
            self.selected_cell = (self.selected_cell[0] + 1, self.selected_cell[1])

    def handle_local_map_events(self, event, keys):
        if event.key == pygame.K_e:
            # Examine tile
            dx, dy = 0, 0
            if keys[pygame.K_w]:
                dy = -1
            elif keys[pygame.K_s]:
                dy = 1
            elif keys[pygame.K_a]:
                dx = -1
            elif keys[pygame.K_d]:
                dx = 1
            self.examine_tile(self.player_x + dx, self.player_y + dy)
        elif event.key == pygame.K_i:
            # Open inventory
            self.open_inventory()
        elif event.key == pygame.K_t:
            # Check time
            current_hour = int(self.time // 60)
            current_minute = int(self.time % 60)
            time_str = f'{current_hour:02d}:{current_minute:02d}'
            self.events.append(f'Current time: {time_str}')
        elif event.key in (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d):
            dx, dy = 0, 0
            if event.key == pygame.K_w:
                dy = -1
            elif event.key == pygame.K_s:
                dy = 1
            elif event.key == pygame.K_a:
                dx = -1
            elif event.key == pygame.K_d:
                dx = 1

            if self.state == 'dungeon':
                self.move_player_dungeon(dx, dy)
            else:
                # Move the player if the tile is walkable
                self.move_player(dx, dy)
            # Move entities after player moves
            self.move_entities()

    
    def move_player_dungeon(self, dx, dy):
        new_x = self.player_x + dx
        new_y = self.player_y + dy

        if 0 <= new_x < len(self.local_map[0]) and 0 <= new_y < len(self.local_map):
            tile_type = self.local_map[new_y][new_x]
            tile = TILES.get(tile_type, TILES['FLOOR'])

            if tile['walkable']:
                self.player_x = new_x
                self.player_y = new_y
                self.events.append(f'Moved to {tile["name"]}')

                if tile_type == 'STAIRS_DOWN':
                    self.dungeon_level += 1
                    if self.dungeon_level > self.max_dungeon_level:
                        self.exit_dungeon()
                    else:
                        self.generate_dungeon_level(self.dungeon_level)
                elif tile_type == 'CHEST':
                    self.open_chest(new_x, new_y)
            else:
                self.events.append(f'Cannot walk into {tile["name"]}')

                if tile_type == 'CHEST':
                    self.open_chest(new_x, new_y)

    def open_chest(self, x, y):
        # Randomly decide the loot
        loot_type = random.choice(['gold', 'item'])
        if loot_type == 'gold':
            amount = random.randint(10, 50)
            self.gold += amount
            self.events.append(f'You found {amount} gold in the chest!')
        else:
            item = random.choice(ITEMS)
            self.inventory.append(item)
            self.events.append(f'You found a {item} in the chest!')

        # Remove the chest from the map
        self.local_map[y][x] = 'FLOOR'

    def connect_rooms(self, dungeon_map, room1, room2):
        # Get the center coordinates of both rooms
        x1, y1 = room1.center_x(), room1.center_y()
        x2, y2 = room2.center_x(), room2.center_y()

        # Randomly decide whether to go horizontal first or vertical
        if random.choice([True, False]):
            # Horizontal then vertical
            self.create_h_tunnel(dungeon_map, x1, x2, y1)
            self.create_v_tunnel(dungeon_map, y1, y2, x2)
        else:
            # Vertical then horizontal
            self.create_v_tunnel(dungeon_map, y1, y2, x1)
            self.create_h_tunnel(dungeon_map, x1, x2, y2)


    def exit_dungeon(self):
        self.events.append('You have reached the end of the dungeon.')
        # Transition to boss map or exit back to the world map
        self.state = 'local_map'
        # Return to the dungeon entrance location
        self.player_x, self.player_y = self.dungeon_entrance_position
        # Restore local map, entities, etc.

    def spawn_dungeon_enemies(self):
        num_enemies = random.randint(5, 10)
        for _ in range(num_enemies):
            while True:
                x = random.randint(0, LOCAL_MAP_WIDTH - 1)
                y = random.randint(0, LOCAL_MAP_HEIGHT - 1)
                if self.local_map[y][x] == 'FLOOR' and (x != self.player_x or y != self.player_y):
                    enemy_type = random.choice(['Goblin', 'Snake', 'Bat'])
                    self.enemies.append(Enemy(x, y, enemy_type))
                    break


    def move_entities(self):
        time_of_day = self.get_time_of_day()
        for enemy in self.enemies:
            enemy.move(self.player_x, self.player_y, self.local_map, time_of_day)
            # Check if enemy has caught the player
            if enemy.x == self.player_x and enemy.y == self.player_y:
                self.start_combat(enemy)
        for villager in self.villagers:
            villager.move(self.local_map)
            # Check if player is interacting with villager
            if villager.x == self.player_x and villager.y == self.player_y:
                self.trade_with_villager(villager)

    def move_player(self, dx, dy):
        new_x = self.player_x + dx
        new_y = self.player_y + dy

        # Check for map boundaries
        if new_x < 0:
            # Move to the left cell
            self.leave_region(-1, 0)
            return
        elif new_x >= LOCAL_MAP_WIDTH:
            # Move to the right cell
            self.leave_region(1, 0)
            return
        elif new_y < 0:
            # Move to the upper cell
            self.leave_region(0, -1)
            return
        elif new_y >= LOCAL_MAP_HEIGHT:
            # Move to the lower cell
            self.leave_region(0, 1)
            return

        tile_type = self.local_map[new_y][new_x]
        tile = TILES.get(tile_type, TILES['PLAIN'])

        if tile['walkable']:
            self.player_x = new_x
            self.player_y = new_y
            self.events.append(f'Moved to {tile["name"]}')
            # Handle interactions with enemies, items, etc.
        else:
            self.events.append(f'Cannot walk into {tile["name"]}')

    def enter_dungeon(self):
        self.events.append('You enter the dungeon.')
        self.dungeon_level = 1
        self.max_dungeon_level = random.randint(2, 5)
        self.dungeon_maps = {}
        self.generate_dungeon_level(self.dungeon_level)
        self.state = 'dungeon'

    def generate_dungeon_level(self, level):
        if level in self.dungeon_maps:
            # Load existing level
            dungeon_data = self.dungeon_maps[level]
            self.local_map = dungeon_data['map']
            self.player_x = dungeon_data['player_x']
            self.player_y = dungeon_data['player_y']
            self.enemies = dungeon_data['enemies']
        else:
            # Generate new dungeon level
            self.local_map = self.create_dungeon_map()
            self.player_x, self.player_y = self.find_start_position()
            self.enemies = []
            self.spawn_dungeon_enemies()

            # Place stairs if not last level
            if level < self.max_dungeon_level:
                stair_x, stair_y = self.place_stairs()
                self.local_map[stair_y][stair_x] = 'STAIRS_DOWN'

            # Save the dungeon level
            self.dungeon_maps[level] = {
                'map': self.local_map,
                'player_x': self.player_x,
                'player_y': self.player_y,
                'enemies': self.enemies,
            }


    def create_dungeon_map(self):
        dungeon_map = [['WALL' for _ in range(LOCAL_MAP_WIDTH)] for _ in range(LOCAL_MAP_HEIGHT)]
        self.rooms = []  # Keep track of rooms
        max_rooms = 10
        room_min_size = 6
        room_max_size = 12

        for _ in range(max_rooms):
            w = random.randint(room_min_size, room_max_size)
            h = random.randint(room_min_size, room_max_size)
            x = random.randint(1, LOCAL_MAP_WIDTH - w - 1)
            y = random.randint(1, LOCAL_MAP_HEIGHT - h - 1)
            new_room = Rect(x, y, w, h)

            # Check for overlaps
            failed = False
            for other_room in self.rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break
            if not failed:
                # Create room
                self.create_room(dungeon_map, new_room)
                self.rooms.append(new_room)

                # Connect to previous room
                if len(self.rooms) > 1:
                    prev_room = self.rooms[-2]
                    self.connect_rooms(dungeon_map, prev_room, new_room)
        self.place_chests()

        return dungeon_map

    def place_chests(self):
        num_chests = random.randint(1, len(self.rooms) // 2)  # Up to half the rooms
        chest_rooms = random.sample(self.rooms, num_chests)
        for room in chest_rooms:
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            if self.local_map[y][x] == 'FLOOR':
                self.local_map[y][x] = 'CHEST'



    def create_room(self, dungeon_map, room):
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                dungeon_map[y][x] = 'FLOOR'

    def create_h_tunnel(self, dungeon_map, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            dungeon_map[y][x] = 'FLOOR'

    def create_v_tunnel(self, dungeon_map, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            dungeon_map[y][x] = 'FLOOR'

    def find_start_position(self):
        for y in range(LOCAL_MAP_HEIGHT):
            for x in range(LOCAL_MAP_WIDTH):
                if self.local_map[y][x] == 'FLOOR':
                    return x, y
        # Fallback if no floor found
        return LOCAL_MAP_WIDTH // 2, LOCAL_MAP_HEIGHT // 2

    def place_stairs(self):
        # Choose a random room to place the stairs
        room = random.choice(self.rooms)
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        self.local_map[y][x] = 'STAIRS_DOWN'
        return x, y


    def leave_region(self, dx, dy):
        # Determine new cell coordinates
        cell_x, cell_y = self.current_cell
        new_cell_x = cell_x + dx
        new_cell_y = cell_y + dy

        # Determine entrance direction for new map
        if dx > 0:
            entrance_direction = 'left'  # Moving right, entering from left
        elif dx < 0:
            entrance_direction = 'right'  # Moving left, entering from right
        elif dy > 0:
            entrance_direction = 'up'     # Moving down, entering from top
        elif dy < 0:
            entrance_direction = 'down'   # Moving up, entering from bottom
        else:
            entrance_direction = None

        # Check if the new cell is within the world map bounds
        if 0 <= new_cell_x < WORLD_MAP_WIDTH and 0 <= new_cell_y < WORLD_MAP_HEIGHT:
            # Before leaving, save the current cell's state
            self.save_current_cell_state()

            # Update current cell
            self.current_cell = (new_cell_x, new_cell_y)

            # Generate or load the local map for the new cell
            self.local_map = self.generate_local_map(new_cell_x, new_cell_y, entrance_direction)
            self.events.append(f'Entered new region: {self.local_map_biome}')
        else:
            self.events.append('Cannot leave the world boundaries')

    def start_combat(self, enemy):
        self.state = 'combat'
        self.in_combat = True
        self.current_enemy = enemy
        self.events.append(f'Engaged in combat with {enemy.name}!')

    def save_current_cell_state(self):
        # Save the state of the current cell
        cell_key = self.current_cell
        self.world_cells[cell_key] = {
            'local_map': self.local_map,
            'player_x': self.player_x,
            'player_y': self.player_y,
            'enemies': self.enemies,
            'villagers': self.villagers,
            'biome': self.local_map_biome,
        }

    def combat_loop(self):
        combat_active = True
        while combat_active and self.running:
            # Attack Phase
            damage = self.attack_phase()
            if damage is None:
                # Player quit or window closed
                combat_active = False
                self.running = False
                break
            self.current_enemy.health -= damage
            self.events.append(f'You dealt {damage} damage to the {self.current_enemy.name}.')

            if self.current_enemy.health <= 0:
                self.events.append(f'You defeated the {self.current_enemy.name}!')
                self.xp += self.current_enemy.xp
                self.gold += self.current_enemy.gold
                self.enemies.remove(self.current_enemy)
                self.state = 'local_map'
                self.in_combat = False
                self.current_enemy = None
                combat_active = False
                break

            # Defense Phase
            damage_taken = self.defense_phase()
            if damage_taken is None:
                # Player quit or window closed
                combat_active = False
                self.running = False
                break
            self.health -= damage_taken
            if damage_taken > 0:
                self.events.append(f'You took {damage_taken} damage from the {self.current_enemy.name}.')

            if self.health <= 0:
                self.events.append('You have been defeated!')
                self.running = False  # End the game
                combat_active = False

    def attack_phase(self):
        # Attack mechanic with moving bar
        bar_width = 300
        bar_height = 20
        bar_x = (WINDOW_WIDTH - bar_width) // 2
        bar_y = WINDOW_HEIGHT // 2 - 100
        indicator_width = 10

        indicator_x = bar_x
        indicator_speed = 5  # Pixels per frame
        moving_right = True

        attacking = True
        damage = 0
        while attacking and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Calculate damage based on indicator position
                        center_x = bar_x + bar_width // 2
                        distance_from_center = abs((indicator_x + indicator_width // 2) - center_x)
                        max_distance = bar_width // 2
                        damage_multiplier = 1 - (distance_from_center / max_distance)
                        damage = int((self.attack + random.randint(0, 5)) * damage_multiplier)
                        attacking = False
                        break

            # Move indicator
            if moving_right:
                indicator_x += indicator_speed
                if indicator_x + indicator_width >= bar_x + bar_width:
                    indicator_x = bar_x + bar_width - indicator_width
                    moving_right = False
            else:
                indicator_x -= indicator_speed
                if indicator_x <= bar_x:
                    indicator_x = bar_x
                    moving_right = True

            # Draw attack bar
            self.screen.fill(BLACK)
            self.draw_text(self.screen, f'Combat with {self.current_enemy.name}', 50, 20, RED)
            self.draw_text(self.screen, f'Your HP: {self.health}/{self.max_health}', 50, 50, WHITE)
            self.draw_text(self.screen, f'{self.current_enemy.name} HP: {self.current_enemy.health}/{self.current_enemy.max_health}', 50, 70, WHITE)
            self.draw_text(self.screen, 'Attack Phase: Press SPACE when the indicator is at the center!', 50, bar_y - 40, WHITE)
            pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
            # Center marker
            pygame.draw.line(self.screen, RED, (bar_x + bar_width // 2, bar_y), (bar_x + bar_width // 2, bar_y + bar_height), 2)
            # Indicator
            pygame.draw.rect(self.screen, GREEN, (indicator_x, bar_y, indicator_width, bar_height))
            pygame.display.flip()
            self.clock.tick(FPS)

        return damage

    def defense_phase(self):
        # Defense mechanic with rhythm game
        sequence_length = 5
        arrow_keys = [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]
        arrows = []
        for _ in range(sequence_length):
            arrows.append(random.choice(arrow_keys))

        arrow_images = {
            pygame.K_UP: pygame.transform.scale(self.font.render('↑', True, WHITE), (50, 50)),
            pygame.K_DOWN: pygame.transform.scale(self.font.render('↓', True, WHITE), (50, 50)),
            pygame.K_LEFT: pygame.transform.scale(self.font.render('←', True, WHITE), (50, 50)),
            pygame.K_RIGHT: pygame.transform.scale(self.font.render('→', True, WHITE), (50, 50)),
        }

        current_arrow = 0
        input_time = 1.5  # Time in seconds to input each arrow
        last_time = time.time()
        defending = True
        damage_taken = 0

        while defending and self.running:
            current_time = time.time()
            if current_time - last_time > input_time:
                # Player failed to input in time
                damage_taken += self.current_enemy.attack // sequence_length
                current_arrow += 1
                last_time = current_time
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == arrows[current_arrow]:
                        # Correct key pressed
                        current_arrow += 1
                        last_time = current_time
                    else:
                        # Wrong key pressed
                        damage_taken += self.current_enemy.attack // sequence_length
                        current_arrow += 1
                        last_time = current_time

            if current_arrow >= sequence_length:
                defending = False

            # Draw defense screen
            self.screen.fill(BLACK)
            self.draw_text(self.screen, f'Combat with {self.current_enemy.name}', 50, 20, RED)
            self.draw_text(self.screen, f'Your HP: {self.health}/{self.max_health}', 50, 50, WHITE)
            self.draw_text(self.screen, f'{self.current_enemy.name} HP: {self.current_enemy.health}/{self.current_enemy.max_health}', 50, 70, WHITE)
            self.draw_text(self.screen, 'Defense Phase: Press the arrows in sequence!', 50, WINDOW_HEIGHT // 2 - 100, WHITE)
            for i in range(sequence_length):
                arrow = arrows[i]
                x = WINDOW_WIDTH // 2 - (sequence_length * 30) + i * 60
                y = WINDOW_HEIGHT // 2
                if i < current_arrow:
                    # Already passed
                    arrow_img = arrow_images[arrow].copy()
                    arrow_img.fill(DARK_GRAY, special_flags=pygame.BLEND_RGBA_MULT)
                else:
                    arrow_img = arrow_images[arrow]
                self.screen.blit(arrow_img, (x, y))
            pygame.display.flip()
            self.clock.tick(FPS)

        return damage_taken

    def open_inventory(self):
        # Display inventory screen
        inventory_active = True
        while inventory_active:
            self.screen.fill(BLACK)
            y_offset = 10
            self.draw_text(self.screen, 'Inventory (Press I to exit)', 10, y_offset, WHITE)
            y_offset += 30
            if self.inventory:
                for item in self.inventory:
                    self.draw_text(self.screen, f'- {item}', 10, y_offset, WHITE)
                    y_offset += 20
            else:
                self.draw_text(self.screen, 'Your inventory is empty.', 10, y_offset, WHITE)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_i:
                        inventory_active = False
                elif event.type == pygame.QUIT:
                    self.running = False
                    inventory_active = False

    def examine_tile(self, x, y):
        if 0 <= x < len(self.local_map[0]) and 0 <= y < len(self.local_map):
            tile_type = self.local_map[y][x]
            tile = TILES.get(tile_type, TILES['PLAIN'])
            # Check for enemy at the location
            for enemy in self.enemies:
                if enemy.x == x and enemy.y == y:
                    self.message = f'You see a {enemy.name}'
                    self.events.append(self.message)
                    return
            # Check for villager at the location
            for villager in self.villagers:
                if villager.x == x and villager.y == y:
                    self.message = f'You see a {villager.name}'
                    self.events.append(self.message)
                    return
            self.message = f'You see a {tile["name"]}'
            self.events.append(self.message)
        else:
            self.message = 'Nothing of interest'
            self.events.append(self.message)

    def enter_building(self):
        # Save current map state onto the map stack
        self.map_stack.append({
            'local_map': self.local_map,
            'local_map_biome': self.local_map_biome,
            'player_x': self.player_x,
            'player_y': self.player_y,
            'current_cell': self.current_cell,
            'enemies': self.enemies,
            'villagers': self.villagers,
        })

        # Generate small interior map
        interior_map_size = 20  # Small interior map size
        self.local_map = [[None for _ in range(interior_map_size)] for _ in range(interior_map_size)]
        for y in range(interior_map_size):
            for x in range(interior_map_size):
                if y == 0 or y == interior_map_size -1 or x == 0 or x == interior_map_size -1:
                    self.local_map[y][x] = 'HOUSE_WALL'
                else:
                    self.local_map[y][x] = 'HOUSE_FLOOR'
        # Place door to exit
        self.local_map[interior_map_size -1][interior_map_size // 2] = 'DOOR'  # Door at bottom center
        # Set player's position to just inside the door
        self.player_x = interior_map_size // 2
        self.player_y = interior_map_size -2  # One tile above the door
        self.enemies = []  # No enemies inside buildings
        self.villagers = []
        self.events.append('You have entered a building.')

    def exit_building(self):
        # Pop the previous map state from the map stack
        if self.map_stack:
            prev_map = self.map_stack.pop()
            self.local_map = prev_map['local_map']
            self.local_map_biome = prev_map['local_map_biome']
            self.player_x = prev_map['player_x']
            self.player_y = prev_map['player_y']
            self.current_cell = prev_map['current_cell']
            self.enemies = prev_map['enemies']
            self.villagers = prev_map['villagers']
            self.events.append('You have exited the building.')
        else:
            self.events.append('Cannot exit, no previous map.')

    def trade_with_villager(self, villager):
        # Simple trading interaction
        self.events.append('Trading with villager...')
        trading = True
        while trading and self.running:
            self.screen.fill(BLACK)
            y_offset = 10
            self.draw_text(self.screen, 'Trade Menu (Press B to buy, E to exit)', 10, y_offset, WHITE)
            y_offset += 30
            for item in ITEMS:
                price = ITEM_PRICES[item]
                self.draw_text(self.screen, f'{item}: {price} gold', 10, y_offset, WHITE)
                y_offset += 20
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_b:
                        # Buy item
                        self.buy_item()
                        trading = False
                    elif event.key == pygame.K_e:
                        trading = False
                elif event.type == pygame.QUIT:
                    self.running = False
                    trading = False

    def buy_item(self):
        # Simple item purchase logic
        self.events.append('Select an item to buy:')
        selecting = True
        while selecting and self.running:
            self.screen.fill(BLACK)
            y_offset = 10
            self.draw_text(self.screen, 'Select Item to Buy (Press item number, E to exit)', 10, y_offset, WHITE)
            y_offset += 30
            for idx, item in enumerate(ITEMS):
                price = ITEM_PRICES[item]
                self.draw_text(self.screen, f'{idx+1}. {item}: {price} gold', 10, y_offset, WHITE)
                y_offset += 20
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e:
                        selecting = False
                    elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                        idx = int(event.unicode) - 1
                        if idx < len(ITEMS):
                            item = ITEMS[idx]
                            price = ITEM_PRICES[item]
                            if self.gold >= price:
                                self.gold -= price
                                self.inventory.append(item)
                                self.events.append(f'Bought {item} for {price} gold.')
                            else:
                                self.events.append('Not enough gold.')
                            selecting = False
                elif event.type == pygame.QUIT:
                    self.running = False
                    selecting = False

    def draw_text(self, surface, text, x, y, color=WHITE):
        text_surface = self.font.render(text, True, color)
        surface.blit(text_surface, (x, y))

    def draw(self):
        if self.state == 'combat':
            self.combat_loop()
        elif self.state == 'main_menu':
            self.draw_main_menu()
        else:
            self.screen.fill(BLACK)
            if self.state == 'world_map' or self.state == 'map_mode':
                self.draw_world_map()
                if self.state == 'map_mode':
                    # Indicate current cell
                    x, y = self.current_cell
                    rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(self.screen, YELLOW, rect, 2)
            elif self.state == 'local_map' or self.state == 'dungeon':
                self.draw_local_map()
                self.draw_panel()
            if self.command_mode:
                self.draw_command_input()
            pygame.display.flip()

    def draw_main_menu(self):
        self.screen.fill(BLACK)
        title_font = pygame.font.SysFont(FONT_NAME, 72)
        subtitle_font = pygame.font.SysFont(FONT_NAME, 36)
        title_surface = title_font.render('Valdmir', True, WHITE)
        subtitle_surface = subtitle_font.render('Press any key to start', True, WHITE)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        subtitle_rect = subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(title_surface, title_rect)
        self.screen.blit(subtitle_surface, subtitle_rect)
        pygame.display.flip()

    def draw_command_input(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        # Draw command input box
        input_box = pygame.Rect(50, WINDOW_HEIGHT // 2 - 20, WINDOW_WIDTH - 100, 40)
        pygame.draw.rect(self.screen, WHITE, input_box, 2)
        command_text = self.font.render(self.command_input, True, WHITE)
        self.screen.blit(command_text, (input_box.x + 10, input_box.y + 10))
        prompt_text = self.font.render('Enter command:', True, WHITE)
        self.screen.blit(prompt_text, (input_box.x, input_box.y - 30))

    def draw_world_map(self):
        for y in range(WORLD_MAP_HEIGHT):
            for x in range(WORLD_MAP_WIDTH):
                cell_data = self.world_map[y][x]
                biome = cell_data['biome']
                color = BIOME_COLORS[biome]
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, BLACK, rect, 1)  # Cell border
                if cell_data['town']:
                    # Draw town marker
                    pygame.draw.circle(self.screen, YELLOW, rect.center, CELL_SIZE // 4)

        # Highlight selected cell
        x, y = self.selected_cell
        rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(self.screen, WHITE, rect, 2)

        # Instructions
        if self.state == 'world_map':
            self.draw_text(self.screen, 'Use WASD to select a starting location and press ENTER.', 10, WINDOW_HEIGHT - 60, WHITE)
        else:
            self.draw_text(self.screen, 'World Map (Press M to return)', 10, WINDOW_HEIGHT - 60, WHITE)
        self.draw_text(self.screen, 'Biomes: Plains (green), Forest (dark green), Mountains (gray), Desert (tan), Water (blue)', 10, WINDOW_HEIGHT - 40, WHITE)
        self.draw_text(self.screen, 'Towns are marked with yellow circles.', 10, WINDOW_HEIGHT - 20, WHITE)

    def draw_local_map(self):
        # Calculate the offset to keep the player centered
        half_viewport_width = VIEWPORT_WIDTH // 2
        half_viewport_height = VIEWPORT_HEIGHT // 2

        offset_x = self.player_x - half_viewport_width
        offset_y = self.player_y - half_viewport_height

        # Clamp the offset so we don't go out of bounds
        offset_x = max(0, min(offset_x, len(self.local_map[0]) - VIEWPORT_WIDTH))
        offset_y = max(0, min(offset_y, len(self.local_map) - VIEWPORT_HEIGHT))

        for y in range(VIEWPORT_HEIGHT):
            for x in range(VIEWPORT_WIDTH):
                map_x = x + offset_x
                map_y = y + offset_y

                if 0 <= map_x < len(self.local_map[0]) and 0 <= map_y < len(self.local_map):
                    tile_type = self.local_map[map_y][map_x]
                    tile = TILES.get(tile_type, TILES['PLAIN'])
                    char = tile['char']
                    color = tile['color']

                    draw_x = x * TILE_SIZE
                    draw_y = y * TILE_SIZE

                    self.draw_text(self.screen, char, draw_x, draw_y, color)

        # Draw enemies
        for enemy in self.enemies:
            if offset_x <= enemy.x < offset_x + VIEWPORT_WIDTH and offset_y <= enemy.y < offset_y + VIEWPORT_HEIGHT:
                draw_x = (enemy.x - offset_x) * TILE_SIZE
                draw_y = (enemy.y - offset_y) * TILE_SIZE
                self.draw_text(self.screen, enemy.char, draw_x, draw_y, enemy.color)

        # Draw villagers
        for villager in self.villagers:
            if offset_x <= villager.x < offset_x + VIEWPORT_WIDTH and offset_y <= villager.y < offset_y + VIEWPORT_HEIGHT:
                draw_x = (villager.x - offset_x) * TILE_SIZE
                draw_y = (villager.y - offset_y) * TILE_SIZE
                self.draw_text(self.screen, villager.char, draw_x, draw_y, villager.color)

        # Draw player at the center of the viewport
        player_draw_x = (self.player_x - offset_x) * TILE_SIZE
        player_draw_y = (self.player_y - offset_y) * TILE_SIZE
        self.draw_text(self.screen, self.player_char, player_draw_x, player_draw_y, self.player_color)

    def draw_panel(self):
        if not self.hud_visible:
            return  # Do not draw HUD if it's hidden

        panel_x = VIEWPORT_WIDTH * TILE_SIZE
        panel_width = WINDOW_WIDTH - panel_x
        pygame.draw.rect(self.screen, PANEL_BG, (panel_x, 0, panel_width, WINDOW_HEIGHT))

        y_offset = 10
        x_offset = panel_x + 10

        # Stats
        draw_text(self.screen, 'Stats', x_offset, y_offset, PANEL_TEXT)
        y_offset += 20
        draw_text(self.screen, f'Level: {self.level}', x_offset, y_offset, PANEL_TEXT)
        y_offset += 20
        draw_text(self.screen, f'XP: {self.xp}', x_offset, y_offset, PANEL_TEXT)
        y_offset += 20
        draw_text(self.screen, f'Gold: {self.gold}', x_offset, y_offset, PANEL_TEXT)
        y_offset += 20

        # Health
        y_offset += 10
        draw_text(self.screen, 'Health', x_offset, y_offset, PANEL_TEXT)
        y_offset += 20
        draw_text(self.screen, f'HP: {self.health}/{self.max_health}', x_offset, y_offset, PANEL_TEXT)
        y_offset += 20

        # Inventory
        y_offset += 10
        draw_text(self.screen, 'Inventory (Press I)', x_offset, y_offset, PANEL_TEXT)
        y_offset += 20
        if self.inventory:
            for item in self.inventory:
                draw_text(self.screen, f'- {item}', x_offset, y_offset, PANEL_TEXT)
                y_offset += 20
        else:
            draw_text(self.screen, 'Empty', x_offset, y_offset, PANEL_TEXT)
            y_offset += 20

        # Events
        y_offset += 10
        draw_text(self.screen, 'Events', x_offset, y_offset, PANEL_TEXT)
        y_offset += 20
        panel_height = WINDOW_HEIGHT - y_offset - 20
        lines_to_show = panel_height // 20
        events_to_show = self.events[-lines_to_show:]
        for event in events_to_show:
            wrapped_text = textwrap.wrap(event, width=30)  # Adjust width as needed
            for line in wrapped_text:
                draw_text(self.screen, line, x_offset, y_offset, PANEL_TEXT)
                y_offset += 20
                if y_offset > WINDOW_HEIGHT - 20:
                    break

        # Message (for examine action)
        if self.message:
            y_offset += 20
            self.draw_text(self.screen, self.message, x_offset, y_offset, PANEL_TEXT)
            self.message = ''  # Clear message after displaying

if __name__ == '__main__':
    game = Game()
    game.run()
