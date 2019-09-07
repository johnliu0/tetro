import sys
import tkinter as tk
from grid import Grid
from tetromino import TetrominoManager

class Tetro(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.master = master

        # Tetris grid dimensions
        self.grid_width = None
        self.grid_height = None
        # lookahead Tetromino
        self.enable_lookaheads = None
        # width of one cell in pixels
        self.cell_width = 35

        self.load_props()
        self.pack()
        self.load_gui()

        self.tetromino_manager = TetrominoManager.get_instance()
        self.tetromino_manager.load_tetrominoes('shapes.txt')

        self.tetris_instances = [
            Grid(self.grid_width, self.grid_height, self.enable_lookaheads)]
        self.game_running = True
        self.game_loop()

    # initializes tkinter window
    def load_gui(self):
        self.pack()
        self.tetris_canvas = tk.Canvas(self,
            height=(self.cell_width*self.grid_height),
            width=(self.cell_width*self.grid_width))
        self.tetris_canvas.pack(side="top")

        self.master.bind("<Key>", self.handle_key_event)

    # loads game options from the properties file
    def load_props(self):
        with open('properties.txt', 'r') as f:
            for line in f:
                line = line.strip()

                # ignore blank lines and comments
                if len(line) == 0 or line[0] == '#':
                    continue


                # parse key=value
                idx_equals = line.find('=')
                if idx_equals == -1:
                    print(f"Line corrupt: {line}")
                key = line[:idx_equals]
                value = line[idx_equals + 1:]

                if key == "grid_width":
                    self.grid_width = int(value)
                elif key == "grid_height":
                    self.grid_height = int(value)
                elif key == "enable_lookaheads":
                    self.enable_lookaheads = value == "True"

    # main game loop
    def game_loop(self):
        self.tetris_instances[0].update()
        self.render()

        if self.game_running:
            self.after(1000, self.game_loop)

    def render(self):
        self.tetris_canvas.delete("all")
        self.tetris_instances[0].render(self.tetris_canvas, self.cell_width)

    # handle keyboard input
    def handle_key_event(self, event):
        if event.char == 'a':
            self.tetris_instances[0].move_left()
            self.render()
        elif event.char == 'd':
            self.tetris_instances[0].move_right()
            self.render()
        elif event.char == 's':
            self.tetris_instances[0].move_down()
            self.render()
        elif event.char == 'w':
            self.tetris_instances[0].rotate()
            self.render()
        elif event.char == ' ':
            self.tetris_instances[0].drop_tetromino()
            self.render()

print(sys.argv[0])

if __name__ == "__main__":
    root = tk.Tk()
    app = Tetro(root)
    app.mainloop()
