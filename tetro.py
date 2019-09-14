import sys
import time
import tkinter as tk
from random import randint
from game import Game
from neuralnetwork import (NeuralNetwork,
    generate_neural_network,
    compute_fitness, crossover, mutate)
from tetromino import TetrominoManager

class Tetro(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.master = master

        # Tetris grid dimensions
        self.grid_width = None
        self.grid_height = None
        self.population_size = None
        self.num_parents = None
        self.mutate_rate = None
        # lookahead Tetromino
        self.enable_lookaheads = None
        # width of one cell in pixels
        self.cell_width = 35

        self.tetris_instances = []
        self.neural_networks = []
        # index of the tetris game that is currently being rendered to screen
        self.current_spectating_idx = 0
        self.generations = 0

        self.load_props()
        self.pack()
        self.load_gui()

        self.tetromino_manager = TetrominoManager.get_instance()
        self.tetromino_manager.load_tetrominoes('shapes.txt')
        self.generate_games(self.population_size)

        self.game_running = True
        self.update_gui_title()
        self.start_game_loop()

        print('STARTING GENERATION: 0')

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

                if key == 'grid_width':
                    self.grid_width = int(value)
                elif key == 'grid_height':
                    self.grid_height = int(value)
                elif key == 'population_size':
                    self.population_size = int(value)
                elif key == 'num_parents':
                    self.num_parents = int(value)
                elif key == 'mutate_rate':
                    self.mutate_rate = float(value)
                elif key == 'enable_lookaheads':
                    self.enable_lookaheads = value == 'True'

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
        self.update_gui_title()

        if self.game_running:
            self.after(1, self.game_loop)

    # updates all Tetris instances once
    # i.e. make all blocks fall down one block
    def update_game(self):
        for i, inst in enumerate(self.tetris_instances):
            inst.update()

    # activates all neural networks once
    def update_ai(self):
        all_lost = True
        for inst, network in zip(self.tetris_instances, self.neural_networks):
            if inst.lost:
                continue
            all_lost = False
            # prepare input data for network
            # -1: occupied, 0: empty, 1: occupied by current tetromino
            tetromino = inst.current_tetromino
            grid = [[(0 if elem == 0 else -1) for elem in col] for col in inst.grid]
            pos_x = inst.current_tetromino.get_pos_x()
            pos_y = inst.current_tetromino.get_pos_y()
            block_data = inst.current_tetromino.get_block_data()
            for x in range(len(block_data)):
                for y in range(len(block_data[0])):
                    if block_data[x][y]:
                        # transform tetromino coordinates to grid coordinates
                        grid[x + pos_x][y + pos_y] = 1

            network_output = network.activate(grid)

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
                # drop
                inst.drop_tetromino()
            else:
                # rotate
                inst.rotate_tetromino()

        if all_lost:
            self.next_generation()

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
            self.neural_networks.append(generate_neural_network(self.grid_width, self.grid_height))

    def next_generation(self):
        self.generations += 1
        print(f'STARTING GENERATION: {self.generations}')
        fitness_scores = [(compute_fitness(inst), i) for i, inst in enumerate(self.tetris_instances)]
        self.tetris_instances.clear()
        list.sort(fitness_scores, key=lambda elem: elem[0])
        highest = fitness_scores[-self.num_parents:]
        num_children = 0
        new_neural_networks = []

        print(highest)

        # crossover every pair
        for i in range(self.population_size):
            # randomly select two different parents
            idx1 = randint(0, self.num_parents - 1)
            idx2 = idx1
            while idx2 == idx1:
                idx2 = randint(0, self.num_parents - 1)
            # crossover parents and produce a new neural network
            self.tetris_instances.append(
                Game(self.grid_width, self.grid_height, self.enable_lookaheads))
            new_network = crossover(self.neural_networks[highest[idx1][1]],
                self.neural_networks[highest[idx2][1]])
            mutate(new_network, self.mutate_rate)
            new_neural_networks.append(new_network)

        self.neural_networks.clear()
        self.neural_networks = new_neural_networks

    # updates the GUI window title with helpful information
    def update_gui_title(self):
        self.master.title(
                f'Tetro | Gen: {self.generations} ' +
                f'Viewing: {self.current_spectating_idx + 1}/{self.population_size} ' +
                ('(LOST)' if self.tetris_instances[self.current_spectating_idx].lost else '(ALIVE)'))

    # handle keyboard input
    def handle_key_event(self, event):
        # switch between Tetris instances
        if event.char == 'j': # view previous neural network
            self.current_spectating_idx -= 1
            self.current_spectating_idx %= len(self.tetris_instances)
            self.render()
        elif event.char == 'k': # view next neural network
            self.current_spectating_idx += 1
            self.current_spectating_idx %= len(self.tetris_instances)
            self.render()
        elif event.char == 'n': # generate new Tetris games
            self.generate_games(self.population_size)
            self.render()
        self.update_gui_title()

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
            self.tetris_instances[0].rotate_tetromino()
            self.render()
        elif event.char == ' ':
            self.tetris_instances[0].drop_tetromino()
            self.render()"""

print(sys.argv[0])

if __name__ == "__main__":
    root = tk.Tk()
    app = Tetro(root)
    app.mainloop()
