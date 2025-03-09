# This is intended for pygame-ce (PyGame Community Edition)
# It may NOT WORK or might be slower, when using normal PyGame.
# https://github.com/pygame-community/pygame-ce
# pip install pygame-ce

from numpy import block
import pygame as pg
import pygame_gui
from assets.colors import *
from helper import *

pg.init(); pg.font.init()


WIDTH, HEIGHT = 800, 600

# Setup
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Vacuum Map")
clock = pg.time.Clock()
manager = pygame_gui.UIManager((WIDTH, HEIGHT))

FPS = 30

radio_tools = pygame_gui.elements.UISelectionList(
    relative_rect=pg.Rect((0, 0), (100, 46)),
    item_list=["Vacuum", "Obstacle"],
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

    def process_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            
            if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
                match event.text.lower():
                    case "vacuum":
                        self.current_draw_tool = 2
                        
                    case "obstacle":
                        self.current_draw_tool = 1
                        
                    case _:
                        self.current_draw_tool = -1
                
            manager.process_events(event)

    def grid(self):
        grid_width = self.grid_size * self.block_size
        grid_height = self.grid_size * self.block_size

        offset_x = (WIDTH - grid_width) // 2
        offset_y = (HEIGHT - grid_height) // 2

        for x in range(offset_x, offset_x + grid_width + 1, self.block_size):
            for y in range(offset_y, offset_y + grid_height + 1, self.block_size):
                rect = pg.Rect(x, y, self.block_size, self.block_size)
                pg.draw.rect(self.screen, color=GRID_LINE, rect=rect, width=1)


    
    def debug_menu(self):
        fps = clock.get_fps()
        fps = round(fps)

        screen.blit(render_text(f"FPS: {str(fps)} | Grid Size: {str(self.grid_size)} | Block Size: {str(self.block_size)} | Tool: {self.current_draw_tool}", 22), (5, HEIGHT - 24))

    def process_rendering(self):
        screen.fill(BACKGROUND)
        self.grid()
        self.debug_menu()

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
