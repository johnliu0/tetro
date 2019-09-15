import sys
import time
import tkinter as tk
from copy import deepcopy
from random import randint
from game import Game
from neuralnetwork import (NeuralNetwork,
    generate_neural_network,
    compute_fitness, crossover, mutate)
from tetromino import TetrominoManager, Tetromino

class Tetro(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.master = master
        # basic Tetris and genetic algorithm properties
        self.grid_width = 0
        self.grid_height = 0
        self.population_size = 0
        self.num_parents = 0
        self.mutate_rate = 0
        self.cell_width = 35
        # active Tetris games and neural networks
        self.tetris_instances = []
        self.neural_networks = []
        # index of the tetris game that is currently being rendered to screen
        self.current_spectating_idx = 0
        self.generations = 0
        # load properties from file and init gui
        self.load_props()
        self.pack()
        self.load_gui()

        self.tmino_manager = TetrominoManager.get_instance()
        self.tmino_manager.load_tetrominoes('shapes.txt', self.grid_width, self.grid_height)
        self.before_time = 0
        self.game_running = True
        self.generate_games(self.population_size)
        self.game_loop()

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

    # main game loop
    def game_loop(self):
        self.current_time = time.perf_counter()
        delta_time = self.current_time - self.before_time
        self.before_time = self.current_time

        self.update()
        self.update_gui_title()
        self.render()

        if self.game_running:
            self.after(10, self.game_loop)

    def update(self):
        all_lost = True
        # compute all possible tetromino placements for each Tetris instance
        # and choose the move that best optimizes the Tetris score
        for inst, network in zip(self.tetris_instances, self.neural_networks):
            # first update the Tetris instance
            inst.update()
            if inst.lost:
                continue
            all_lost = False
            tmino_id = inst.current_tmino.data.id

            # convert grid to a binary representation
            # where True is an occupied cell and False is an empty cell
            grid = []
            for x in range(self.grid_width):
                grid.append([])
                for y in range(self.grid_height):
                    grid[-1].append(inst.grid[x][y] != 0)

            # keep track of the best move that can be made
            # a list in the format: (score, x_pos, y_pos, None)
            best_move = [float('-inf'), 0, 0, None]
            # try each rotation
            for rotation in range(4):
                # initialize the rotated tetromino
                tmino = Tetromino(self.tmino_manager.get_tetromino_type(tmino_id, rotation))
                # try each possible column
                for x in range(tmino.data.min_x, tmino.data.max_x + 1):
                    tmino.x_pos = x
                    # find the lowest point that it can drop to
                    for y in range(tmino.data.min_y, tmino.data.max_y + 2):
                        tmino.y_pos = y
                        # if the tetromino is colliding, then the previous move
                        # is the furthest it could have dropped
                        if inst.is_colliding(tmino):
                            # however if the tetromino was colliding even at
                            # its min y position, then it is not possible
                            # to make a move in this column
                            if tmino.y_pos == tmino.data.min_y:
                                break
                            tmino.y_pos -= 1

                            # add the tetromino to the binary grid
                            for x2 in range(tmino.data.size):
                                for y2 in range(tmino.data.size):
                                    if tmino.data.block_data[x2][y2]:
                                        grid_x = x2 + tmino.x_pos
                                        grid_y = y2 + tmino.y_pos
                                        # check if the tetromino cell is out of bounds
                                        if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
                                            continue
                                        # otherwise update the grid cell with the tetromino cell
                                        grid[grid_x][grid_y] = True

                            # compute a score for this move using the neural network
                            score = network.activate(grid)
                            if score > best_move[0]:
                                best_move = [score, tmino.x_pos, tmino.y_pos, tmino.data]

                            # remove this tetromino from the binary grid
                            for x2 in range(tmino.data.size):
                                for y2 in range(tmino.data.size):
                                    if tmino.data.block_data[x2][y2]:
                                        grid_x = x2 + tmino.x_pos
                                        grid_y = y2 + tmino.y_pos
                                        # check if the tetromino cell is out of bounds
                                        if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
                                            continue
                                        # otherwise
                                        grid[grid_x][grid_y] = False
                            # once we have found a collision, move on to the next column
                            break
            inst.current_tmino = Tetromino(best_move[3], best_move[1], best_move[2])
        if all_lost:
            print((' ').join([str(compute_fitness(inst)) for inst in self.tetris_instances]))

    def render(self):
        self.tetris_canvas.delete("all")
        # render one Tetris game to screen
        self.tetris_instances[self.current_spectating_idx].render(
            self.tetris_canvas, self.cell_width)

    def generate_games(self, num=1):
        self.tetris_instances.clear()
        self.neural_networks.clear()
        for i in range(num):
            self.tetris_instances.append(Game(self.grid_width, self.grid_height))
            self.neural_networks.append(generate_neural_network(self.grid_width, self.grid_height))

    def update_gui_title(self):
        self.master.title(
                f'Tetro | Gen: {self.generations} ' +
                f'Viewing: {self.current_spectating_idx + 1}/{self.population_size} ' +
                ('(LOST)' if self.tetris_instances[self.current_spectating_idx].lost else '(ALIVE)'))

    """
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
    """
    # handle keyboard input
    def handle_key_event(self, event):
        # switch between Tetris instances
        if event.char == 'j': # view previous neural network
            self.current_spectating_idx -= 1
            self.current_spectating_idx %= len(self.tetris_instances)
        elif event.char == 'k': # view next neural network
            self.current_spectating_idx += 1
            self.current_spectating_idx %= len(self.tetris_instances)
        elif event.char == 'n': # generate new Tetris games
            #self.generate_games(self.population_size)
            pass
        elif event.char == 'a':
            self.tetris_instances[self.current_spectating_idx].move_left()
        elif event.char == 'd':
            self.tetris_instances[self.current_spectating_idx].move_right()
        elif event.char == 's':
            self.tetris_instances[self.current_spectating_idx].move_down()
        elif event.char == 'w':
            self.tetris_instances[self.current_spectating_idx].rotate()
        elif event.char == ' ':
            self.tetris_instances[self.current_spectating_idx].drop()
        self.update_gui_title()
        self.render()

if __name__ == "__main__":
    root = tk.Tk()
    app = Tetro(root)
    app.mainloop()
