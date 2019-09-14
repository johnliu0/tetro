import sys
import time
import tkinter as tk
from game import Game
from neuralnetwork import (NeuralNetwork,
    compute_fitness, crossover, mutate)
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

        self.tetris_instances = []
        self.neural_networks = []
        # index of the tetris game that is currently being rendered to screen
        self.current_spectating_idx = 0
        self.generate_games(1)

        self.game_running = True
        self.start_game_loop()

    # initializes tkinter window
    def load_gui(self):
        self.pack()
        self.tetris_canvas = tk.Canvas(self,
            height=(self.cell_width * self.grid_height),
            width=(self.cell_width * self.grid_width))
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

    def start_game_loop(self):
        # initialize time variables
        self.before_time = time.perf_counter()
        current_time = 0
        self.game_loop()

    # main game loop
    def game_loop(self):
        self.current_time = time.perf_counter()
        delta_time = self.current_time - self.before_time
        self.before_time = self.current_time

        self.update_game()
        self.update_ai()
        self.render()

        if self.game_running:
            self.after(25, self.game_loop)

    # updates all Tetris instances once
    # i.e. make all blocks fall down one block
    def update_game(self):
        for i, inst in enumerate(self.tetris_instances):
            if compute_fitness(inst) > 0:
                print(f'LINE CLEARED BY: {i}')
            inst.update()

    # activates all neural networks once
    def update_ai(self):
        for inst, network in zip(self.tetris_instances, self.neural_networks):
            if inst.lost:
                continue
            network_output = network.activate(
                [[(0 if elem == 0 else 1) for elem in col] for col in inst.grid],
                inst.current_tetromino.pos_x,
                inst.current_tetromino.pos_y,
                inst.current_tetromino.get_id)

            idx_max = 0
            for i in range(len(network_output)):
                if network_output[i] > network_output[idx_max]:
                    idx_max = i
            if idx_max == 0:
                # go left
                inst.move_left()
            elif idx_max == 1:
                # go right
                inst.move_right()
            elif idx_max == 2:
                # go down
                inst.move_down()
            elif idx_max == 3:
                # drop
                inst.drop_tetromino()
            else:
                # rotate
                inst.rotate_tetromino()

    def render(self):
        self.tetris_canvas.delete("all")
        self.tetris_instances[self.current_spectating_idx].render(self.tetris_canvas, self.cell_width)

    # generates some tetris instances and neural networks
    def generate_games(self, num):
        self.tetris_instances.clear()
        self.neural_networks.clear()
        for i in range(num):
            self.tetris_instances.append(
                Game(self.grid_width, self.grid_height, self.enable_lookaheads))
            self.neural_networks.append(
                NeuralNetwork(
                    self.tetromino_manager.get_num_type_tetrominoes(), self.grid_width, self.grid_height,
                    -2, -1, self.grid_width - 1, self.grid_height - 1))

    # handle keyboard input
    def handle_key_event(self, event):
        # switch between Tetris instances
        if event.char == 'j':
            self.current_spectating_idx += 1
            self.current_spectating_idx %= len(self.tetris_instances)
            self.render()
        elif event.char == 'k': # left arrow
            self.current_spectating_idx -= 1
            self.current_spectating_idx %= len(self.tetris_instances)
            self.render()
        elif event.char == 'n': # generate new Tetris games

            self.generate_games(15)
            self.render()

        """if event.char == 'a':
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
            self.render()"""

print(sys.argv[0])

if __name__ == "__main__":
    root = tk.Tk()
    app = Tetro(root)
    app.mainloop()
