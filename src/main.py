# This is intended for pygame-ce (PyGame Community Edition)
# It may NOT WORK or might be slower, when using normal PyGame.
# https://github.com/pygame-community/pygame-ce
# pip install pygame-ce

import json
import pygame as pg
import pygame_gui
from pygame_gui.windows import UIFileDialog
from assets.colors import *
from helper import *

pg.init()
pg.font.init()

WIDTH, HEIGHT = 800, 600

# Setup
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Vacuum Map")
clock = pg.time.Clock()
manager = pygame_gui.UIManager((WIDTH, HEIGHT))

FPS = 60

tile_map = {}  # Dictionary to store tile states
vacuum_position = None  # Track vacuum position
mouse_down = False  # Track mouse button state
undo_stack = []  # Stack to store previous states for undo functionality

radio_tools = pygame_gui.elements.UISelectionList(
    relative_rect=pg.Rect((0, 0), (100, 66)),
    item_list=["Vacuum", "Obstacle", "Eraser"],
    manager=manager
)

# Resize and position the buttons on the side of the screen
export_json_button = pygame_gui.elements.UIButton(
    relative_rect=pg.Rect((WIDTH - 110, 70), (100, 30)),
    text='Export JSON',
    manager=manager
)

export_png_button = pygame_gui.elements.UIButton(
    relative_rect=pg.Rect((WIDTH - 110, 120), (100, 30)),
    text='Export PNG',
    manager=manager
)

load_json_button = pygame_gui.elements.UIButton(
    relative_rect=pg.Rect((WIDTH - 110, 170), (100, 30)),
    text='Load JSON',
    manager=manager
)

undo_button = pygame_gui.elements.UIButton(
    relative_rect=pg.Rect((WIDTH - 110, 220), (100, 30)),
    text='Undo',
    manager=manager
)

class App:
    def __init__(self, screen: pg.Surface, clock: pg.time.Clock, grid_size: int, block_size: int = 15):
        self.running = True
        self.screen = screen
        self.clock = clock
        self.grid_size = grid_size
        self.block_size = block_size
        self.current_draw_tool = -1
        self.file_dialog = None

    def handle_tile_change(self, pos):
        global vacuum_position
        x, y = pos
        grid_x = (x - (WIDTH - self.grid_size * self.block_size) // 2) // self.block_size
        grid_y = (y - (HEIGHT - self.grid_size * self.block_size) // 2) // self.block_size

        if 0 <= grid_x < self.grid_size and 0 <= grid_y < self.grid_size:
            undo_stack.append((grid_x, grid_y, tile_map.get((grid_x, grid_y), 0)))
            if self.current_draw_tool == 1:
                tile_map[(grid_x, grid_y)] = 1  # OBSTACLE
            elif self.current_draw_tool == 2:
                if vacuum_position is not None:
                    tile_map.pop(vacuum_position, None)
                vacuum_position = (grid_x, grid_y)
                tile_map[vacuum_position] = 2  # VACUUM
            elif self.current_draw_tool == 3:
                tile_map.pop((grid_x, grid_y), None)  # Erase tile (fallback to FLOOR)

    def process_events(self):
        global mouse_down

        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

            if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
                match event.text.lower():
                    case "vacuum":
                        self.current_draw_tool = 2
                    case "obstacle":
                        self.current_draw_tool = 1
                    case "eraser":
                        self.current_draw_tool = 3
                    case _:
                        self.current_draw_tool = -1

            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                mouse_down = True
                self.handle_tile_change(event.pos)

            if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                mouse_down = False

            if event.type == pg.MOUSEMOTION and mouse_down:
                self.handle_tile_change(event.pos)

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == export_json_button:
                    self.export_to_json()
                elif event.ui_element == export_png_button:
                    self.export_to_png()
                elif event.ui_element == load_json_button:
                    self.load_from_json()
                elif event.ui_element == undo_button:
                    self.undo()

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_1:
                    self.current_draw_tool = 1
                elif event.key == pg.K_2:
                    self.current_draw_tool = 2
                elif event.key == pg.K_3:
                    self.current_draw_tool = 3

            if self.file_dialog is not None:
                if event.type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
                    if event.ui_element == self.file_dialog:
                        self.file_dialog_path_picked(event.text)

            manager.process_events(event)

    def grid(self):
        grid_width = self.grid_size * self.block_size
        grid_height = self.grid_size * self.block_size

        offset_x = (WIDTH - grid_width) // 2
        offset_y = (HEIGHT - grid_height) // 2

        # Draw column numbers (above the grid) with smaller font and rotated
        font = pg.font.SysFont('Arial', 12)
        for x in range(self.grid_size):
            label = font.render(str(x), True, (255, 255, 255))
            rotated_label = pg.transform.rotate(label, 45)
            screen.blit(rotated_label, (offset_x + x * self.block_size + self.block_size // 2 - rotated_label.get_width() // 2, offset_y - 20))

        # Draw row numbers (beside the grid) with smaller font and rotated
        for y in range(self.grid_size):
            label = font.render(str(y), True, (255, 255, 255))
            rotated_label = pg.transform.rotate(label, 45)
            screen.blit(rotated_label, (offset_x - 20, offset_y + y * self.block_size + self.block_size // 2 - rotated_label.get_height() // 2))

        for x in range(self.grid_size):
            for y in range(self.grid_size):
                rect = pg.Rect(offset_x + x * self.block_size, offset_y + y * self.block_size, self.block_size, self.block_size)
                tile_value = tile_map.get((x, y), 0)  # Default to FLOOR
                color = FLOOR if tile_value == 0 else OBSTACLE if tile_value == 1 else VACUUM
                pg.draw.rect(self.screen, color, rect)
                pg.draw.rect(self.screen, GRID_LINE, rect, width=1)

    def debug_menu(self):
        fps = round(clock.get_fps())
        screen.blit(render_text(f"FPS: {fps} | Grid Size: {self.grid_size} | Tool: {self.current_draw_tool}", 22), (5, HEIGHT - 24))

    def process_rendering(self):
        screen.fill(BACKGROUND)
        self.grid()
        self.debug_menu()

    def export_to_json(self):
        # Export the grid as a list of lists (0, 1, 2 values)
        export_data = self.get_tile_map_as_array()

        self.file_dialog = UIFileDialog(
            rect=pg.Rect((WIDTH // 2 - 200, HEIGHT // 2 - 150), (400, 300)),
            manager=manager,
            allow_picking_directories=False,
            allow_existing_files_only=False,
            initial_file_path='export.json'
        )

    def export_to_png(self):
        # Export the grid to PNG
        grid_width = self.grid_size * self.block_size
        grid_height = self.grid_size * self.block_size

        offset_x = (WIDTH - grid_width) // 2
        offset_y = (HEIGHT - grid_height) // 2

        surface = pg.Surface((grid_width, grid_height))
        surface.fill((0, 0, 0))  # Fill background with black for the grid

        for x in range(self.grid_size):
            for y in range(self.grid_size):
                rect = pg.Rect(x * self.block_size, y * self.block_size, self.block_size, self.block_size)
                tile_value = tile_map.get((x, y), 0)  # Default to FLOOR
                color = FLOOR if tile_value == 0 else OBSTACLE if tile_value == 1 else VACUUM
                pg.draw.rect(surface, color, rect)
                pg.draw.rect(surface, GRID_LINE, rect, width=1)

        self.file_dialog = UIFileDialog(
            rect=pg.Rect((WIDTH // 2 - 200, HEIGHT // 2 - 150), (400, 300)),
            manager=manager,
            allow_picking_directories=False,
            allow_existing_files_only=False,
            initial_file_path='export.png'
        )

    def load_from_json(self):
        self.file_dialog = UIFileDialog(
            rect=pg.Rect((WIDTH // 2 - 200, HEIGHT // 2 - 150), (400, 300)),
            manager=manager,
            allow_picking_directories=False,
            allow_existing_files_only=True,
            initial_file_path='export.json'
        )

    def file_dialog_path_picked(self, path):
        if path.endswith('.json'):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    for x in range(self.grid_size):
                        for y in range(self.grid_size):
                            value = data[x][y]
                            if value == 0:
                                tile_map[(x, y)] = 0  # FLOOR
                            elif value == 1:
                                tile_map[(x, y)] = 1  # OBSTACLE
                            elif value == 2:
                                tile_map[(x, y)] = 2  # VACUUM
                print(f"Grid loaded from {path}")
            except FileNotFoundError:
                print("No file found.")
        elif path.endswith('.png'):
            pg.image.save(self.get_surface_for_export(), path)
            print(f"Grid exported to {path}")
        self.file_dialog = None

    def get_surface_for_export(self):
        grid_width = self.grid_size * self.block_size
        grid_height = self.grid_size * self.block_size

        surface = pg.Surface((grid_width, grid_height))
        surface.fill((0, 0, 0))  # Fill background with black for the grid

        for x in range(self.grid_size):
            for y in range(self.grid_size):
                rect = pg.Rect(x * self.block_size, y * self.block_size, self.block_size, self.block_size)
                tile_value = tile_map.get((x, y), 0)  # Default to FLOOR
                color = FLOOR if tile_value == 0 else OBSTACLE if tile_value == 1 else VACUUM
                pg.draw.rect(surface, color, rect)
                pg.draw.rect(surface, GRID_LINE, rect, width=1)

        return surface

    def get_tile_map_as_array(self):
        # Convert tile_map into a 2D array representation (0, 1, 2)
        return [[tile_map.get((x, y), 0) for y in range(self.grid_size)] for x in range(self.grid_size)]

    def undo(self):
        if undo_stack:
            x, y, value = undo_stack.pop()
            if value == 0:
                tile_map.pop((x, y), None)
            else:
                tile_map[(x, y)] = value

    def run(self):
        while self.running:
            td = clock.tick(FPS) / 1000.0
            self.process_events()
            self.process_rendering()
            manager.update(td)
            manager.draw_ui(self.screen)
            pg.display.flip()

if __name__ == '__main__':
    app = App(screen, clock, 32)
    app.run()
