import sys
import time
import tkinter as tk
import math
import multiprocessing
from copy import deepcopy
from random import randint
from game import Game
from ai import TetrisAI
from neuralnetwork import (NeuralNetwork,
    generate_neural_network,
    compute_fitness, crossover, mutate)
from tetromino import TetrominoManager, Tetromino

print(multiprocessing.cpu_count())

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
        self.tetris_ais = []
        # index of the tetris game that is currently being rendered to screen
        self.current_spectating_idx = 0
        self.generation = 0
        # load properties from file and init gui
        self.load_props()
        self.pack()
        self.load_gui()

        self.tmino_manager = TetrominoManager.get_instance()
        self.tmino_manager.load_tetrominoes('shapes.txt', self.grid_width, self.grid_height)
        self.before_time = 0
        self.game_running = True
        self.print_starting_generation()
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
            # sleep for 1 ms so that your CPU does not blow up!
            self.after(1, self.game_loop)

    def update(self):
        all_lost = True
        # compute all possible tetromino placements for each Tetris instance
        # and choose the move that best optimizes the Tetris score
        for inst, ai in zip(self.tetris_instances, self.tetris_ais):
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

                            # compute a score for this move using the neural network
                            score = ai.compute_score(grid, tmino)
                            if score > best_move[0]:
                                best_move = [score, tmino.x_pos, tmino.y_pos, tmino.data]

                            """# try moving to the sides and seeing if it produces a better score
                            tmino.x_pos -= 1
                            if not inst.is_colliding(tmino):
                                # check to see if it is grounded properly
                                tmino.y_pos += 1
                                if not inst.is_colliding(tmino):
                                    tmino.y_pos -= 1
                                    break
                                tmino.y_pos -= 1
                                # compute the score for this new position
                                score = ai.compute_score(grid, tmino)
                                if score > best_move[0]:
                                    best_move = [score, tmino.x_pos, tmino.y_pos, tmino.data]
                            tmino.x_pos += 2
                            if not inst.is_colliding(tmino):
                                tmino.y_pos += 1
                                if not inst.is_colliding(tmino):
                                    tmino.y_pos -= 1
                                    break
                                tmino.y_pos -= 1
                                score = ai.compute_score(grid, tmino)
                                if score > best_move[0]:
                                    best_move = [score, tmino.x_pos, tmino.y_pos, tmino.data]"""

                            # once we have found a collision, move on to the next column
                            break
            inst.current_tmino = Tetromino(best_move[3], best_move[1], best_move[2])
        if all_lost:
            self.next_generation()
        # switch the view to the next live Tetris game if the current Tetris game has lost
        if self.tetris_instances[self.current_spectating_idx].lost:
            for i in range(self.population_size):
                if not self.tetris_instances[i].lost:
                    self.current_spectating_idx = i
                    break


    def render(self):
        self.tetris_canvas.delete("all")
        # render one Tetris game to screen
        self.tetris_instances[self.current_spectating_idx].render(
            self.tetris_canvas, self.cell_width)

    def generate_games(self, num=1):
        self.tetris_instances.clear()
        self.tetris_ais.clear()
        for i in range(num):
            self.tetris_instances.append(Game(self.grid_width, self.grid_height))
            self.tetris_ais.append(TetrisAI(self.grid_width, self.grid_height, []))

    def next_generation(self):
        self.generation += 1

        fitness_scores = [(inst.lines_cleared, i) for i, inst in enumerate(self.tetris_instances)]

        print('Lines cleared: ', (' ').join([str(elem[0]) for elem in fitness_scores]))
        avg_all = 0
        for elem in fitness_scores:
            avg_all += elem[0]
        avg_all /= len(fitness_scores)
        print('Lines cleared average: ', avg_all)

        self.tetris_instances.clear()
        list.sort(fitness_scores, key=lambda elem: elem[0])
        highest = fitness_scores[-self.num_parents:]
        highest.reverse()

        print('Most lines cleared: ', (' ').join([str(elem[0]) for elem in highest]))
        avg_most = 0
        for elem in highest:
            avg_most += elem[0]
        avg_most /= len(highest)
        print('Most lines cleared average: ', avg_most)

        print('Weights of most cleared: ', self.tetris_ais[highest[0][1]].weights)

        if avg_most < 0.0001:
            self.generate_games(self.population_size)
            return

        num_children = 0
        new_neural_networks = []

        # crossover every pair
        for i in range(self.population_size):
            # randomly select two different parents
            idx1 = randint(0, self.num_parents - 1)
            idx2 = idx1
            while idx2 == idx1:
                idx2 = randint(0, self.num_parents - 1)
            # crossover parents and produce a new neural network
            self.tetris_instances.append(Game(self.grid_width, self.grid_height))
            new_network = self.tetris_ais[highest[idx1][1]].crossover(self.tetris_ais[highest[idx2][1]])
            new_network.mutate(self.mutate_rate)
            new_neural_networks.append(new_network)

        self.tetris_ais.clear()
        self.tetris_ais = new_neural_networks
        self.print_starting_generation()

    def update_gui_title(self):
        self.master.title(
                f'Tetro | Gen: {self.generation} ' +
                f'Viewing: {self.current_spectating_idx + 1}/{self.population_size} ' +
                ('(LOST)' if self.tetris_instances[self.current_spectating_idx].lost else '(ALIVE)'))

    def print_starting_generation(self):
        print()
        print(f'---- Starting Generation {self.generation} -----')

    """
    def render(self):
        self.tetris_canvas.delete("all")
        self.tetris_instances[self.current_spectating_idx].render(self.tetris_canvas, self.cell_width)

   # generates some tetris instances and neural networks
    def generate_games(self, num):
        self.tetris_instances.clear()
        self.tetris_ais.clear()
        for i in range(num):
            self.tetris_instances.append(
                Game(self.grid_width, self.grid_height, self.enable_lookaheads))
            self.tetris_ais.append(generate_neural_network(self.grid_width, self.grid_height))

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
