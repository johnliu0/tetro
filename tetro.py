import sys
import time
import math
import tkinter as tk
import multiprocessing as mp

import pygame

from copy import deepcopy
from random import random, randint
from game import Game
from ai import TetrisAI, compute_fitness
from tetromino import TetrominoManager, Tetromino

class Tetro(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.master = master
        # basic Tetris and genetic algorithm properties
        self.grid_width = 0
        self.grid_height = 0
        self.population_size = 0
        self.selection_size = 0
        self.crossover_rate = 0
        self.mutate_rate = 0
        self.cell_width = 7
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
        self.pause = False
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
                    print(f'Line corrupt: {line}')
                key = line[:idx_equals]
                value = line[idx_equals + 1:]
                if key == 'grid_width':
                    self.grid_width = int(value)
                elif key == 'grid_height':
                    self.grid_height = int(value)
                elif key == 'population_size':
                    self.population_size = int(value)
                elif key == 'selection_size':
                    self.selection_size = int(value)
                elif key == 'crossover_rate':
                    self.crossover_rate = float(value)
                elif key == 'mutate_rate':
                    self.mutate_rate = float(value)

    # main game loop
    def game_loop(self):
        self.current_time = time.perf_counter()
        delta_time = self.current_time - self.before_time
        self.before_time = self.current_time

        print('Time since last update: ', delta_time)

        if not self.pause:
            self.update()

        self.update_gui_title()
        self.render()

        if self.game_running:
            # sleep for 1 ms so that your CPU does not blow up!
            self.after(1, self.game_loop)

    def update(self):
        # first update all tetris instances
        all_lost = True
        for inst in self.tetris_instances:
            inst.update()
            if not inst.lost:
                all_lost = False

        # start next generation if all Tetris instances have lost
        if all_lost:
            self.next_generation()
            return


        # compute moves to make using the AIs
        # the moves are generated with Python's multiprocessing ability
        moves = []
        with mp.Pool() as pool:
            results = []
            for i, inst in enumerate(self.tetris_instances):
                if not inst.lost:
                    results.append((pool.apply_async(self.tetris_ais[i].compute_move, (inst,)), i))
            moves = [(r[0].get(), r[1]) for r in results]

        # finalize moves
        for move in moves:
            self.tetris_instances[move[1]].current_tmino = Tetromino(
                self.tmino_manager.get_tetromino_type(
                    self.tetris_instances[move[1]].current_tmino.data.id,
                    move[0][2]
                ),
                move[0][0], move[0][1]
            );

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

        fitness_scores = [(compute_fitness(inst), i) for i, inst in enumerate(self.tetris_instances)]

        print('Lines cleared: ', self.format_float_list([elem[0] for elem in fitness_scores], num_decimals=0, delimiter=' '))
        avg_all = 0
        for elem in fitness_scores:
            avg_all += elem[0]
        avg_all /= len(fitness_scores)
        print('Lines cleared average: ', '{:.1f}'.format(avg_all))

        self.tetris_instances.clear()
        list.sort(fitness_scores, key=lambda elem: elem[0])
        highest = fitness_scores[-self.num_parents:]
        highest.reverse()

        print('Most lines cleared: ', self.format_float_list([elem[0] for elem in highest], num_decimals=0, delimiter=' '))
        avg_most = 0
        for elem in highest:
            avg_most += elem[0]
        avg_most /= len(highest)
        print('Most lines cleared average: ', '{:.1f}'.format(avg_most))

        print('Most cleared row filled weights: ', self.format_float_list(self.tetris_ais[highest[0][1]].row_filled_weights))
        print('Most cleared hole size weights: ', self.format_float_list(self.tetris_ais[highest[0][1]].hole_size_weights))
        print('Most cleared hole x pos weights: ', self.format_float_list(self.tetris_ais[highest[0][1]].hole_x_pos_weights))
        print('Most cleared hole height weights: ', self.format_float_list(self.tetris_ais[highest[0][1]].hole_height_weights))

        num_children = 0
        new_neural_networks = []

        # crossover every pair
        crossover_probability = 0.8
        while len(new_neural_networks) != self.population_size:

            # randomly select two different parents
            idx1 = randint(0, self.num_parents - 1)
            idx2 = idx1
            while idx2 == idx1:
                idx2 = randint(0, self.num_parents - 1)

            if random() <= crossover_probability:
                # crossover parents and produce a new neural network
                self.tetris_instances.append(Game(self.grid_width, self.grid_height))
                new_network = self.tetris_ais[highest[idx1][1]].crossover(self.tetris_ais[highest[idx2][1]])
                new_network.mutate(self.mutate_rate)
                new_neural_networks.append(new_network)
            else:
                new_neural_networks.append(self.tetris_ais[highest[idx1][1]])

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

    def format_float_list(self, float_list, num_decimals=2, delimiter=', '):
        return delimiter.join([('{:.' + str(num_decimals) + 'f}').format(num) for num in float_list])

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
        elif event.char == 'p':
            self.pause = not self.pause
        self.update_gui_title()
        self.render()

class App:
    def __init__(self):
        # basic Tetris and genetic algorithm properties
        self.grid_width = 0
        self.grid_height = 0
        self.population_size = 0
        self.selection_size = 0
        self.crossover_rate = 0
        self.mutate_rate = 0
        self.generation = 0
        # size of cell in pixels (for rendering)
        self.cell_width = 35
        # active Tetris games and neural networks
        self.tetris_instances = []
        self.tetris_ais = []
        # index of the tetris game that is currently being rendered to screen
        self.current_spectating_idx = 0

        self.load_properties()
        self.init_pygame()

        self.tmino_manager = TetrominoManager.get_instance()
        self.tmino_manager.load_tetrominoes('shapes.txt', self.grid_width, self.grid_height)
        self.game_running = False
        self.game_paused = False

    def start(self):
        self.game_running = True
        self.game_loop()

    def init_pygame(self):
        pygame.init()
        self.pygame_surface = pygame.display.set_mode(
            (self.grid_width * self.cell_width,
            self.grid_height * self.cell_width))

    # loads game options from the properties file
    def load_properties(self):
        with open('properties.txt', 'r') as f:
            for line in f:
                line = line.strip()
                # ignore blank lines and comments
                if len(line) == 0 or line[0] == '#':
                    continue
                # parse key=value
                idx_equals = line.find('=')
                if idx_equals == -1:
                    print(f'Line corrupt: {line}')
                key = line[:idx_equals]
                value = line[idx_equals + 1:]
                if key == 'grid_width':
                    self.grid_width = int(value)
                elif key == 'grid_height':
                    self.grid_height = int(value)
                elif key == 'population_size':
                    self.population_size = int(value)
                elif key == 'selection_size':
                    self.selection_size = int(value)
                elif key == 'crossover_rate':
                    self.crossover_rate = float(value)
                elif key == 'mutate_rate':
                    self.mutate_rate = float(value)

    def game_loop(self):
        self.generate_random_games(self.population_size)
        self.print_starting_generation()
        game_clock = pygame.time.Clock()
        while self.game_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            if not self.game_paused:
                self.update()
            self.render()
            self.update_gui_title()
            pygame.time.wait(10)
            game_clock.tick()

    def update(self):
        # update all tetris instances
        all_lost = True
        for inst, ai in zip(self.tetris_instances, self.tetris_ais):
            inst.update()
            if inst.lost:
                continue
            all_lost = False
            move = ai.compute_move(inst)
            inst.current_tmino = Tetromino(
                self.tmino_manager.get_tetromino_type(
                    inst.current_tmino.data.id,
                    move[2]
                ), move[0], move[1]);

        # start next generation if all Tetris instances have lost
        if all_lost:
            self.next_generation()

        # switch the view to the next live Tetris game if the current Tetris game has lost
        if self.tetris_instances[self.current_spectating_idx].lost:
            for i in range(self.population_size):
                if not self.tetris_instances[i].lost:
                    self.current_spectating_idx = i
                    break
    
    def render(self):
        self.pygame_surface.fill((0, 0, 0))
        self.tetris_instances[self.current_spectating_idx].render(
            self.pygame_surface, self.cell_width)
        pygame.display.flip()

    def generate_random_games(self, num=1):
        self.tetris_instances.clear()
        self.tetris_ais.clear()
        for i in range(num):
            self.tetris_instances.append(Game(self.grid_width, self.grid_height))
            self.tetris_ais.append(TetrisAI(self.grid_width, self.grid_height))

    def next_generation(self):
        self.generation += 1
        fitness_scores = [(compute_fitness(inst), i) for i, inst in enumerate(self.tetris_instances)]
        list.sort(fitness_scores, key=lambda elem: elem[0])
        fitness_scores.reverse()
        avg_all = sum([elem[0] for elem in fitness_scores]) / len(fitness_scores)
        print('Lines cleared: ', self.format_float_list([elem[0] for elem in fitness_scores], num_decimals=0, delimiter=' '))
        print('Lines cleared average: ', self.format_float_list([avg_all]))

        highest_scores = fitness_scores[:self.selection_size]
        avg_most = sum([elem[0] for elem in highest_scores]) / len(highest_scores)
        print('Most lines cleared: ', self.format_float_list([elem[0] for elem in highest_scores], num_decimals=0, delimiter=' '))
        print('Most lines cleared average: ', self.format_float_list([avg_most]))

        print('Most cleared row filled weights: ', self.format_float_list(self.tetris_ais[highest_scores[0][1]].row_filled_weights, brackets=True))
        print('Most cleared hole size weights: ', self.format_float_list(self.tetris_ais[highest_scores[0][1]].hole_size_weights, brackets=True))
        print('Most cleared hole x pos weights: ', self.format_float_list(self.tetris_ais[highest_scores[0][1]].hole_x_pos_weights, brackets=True))
        print('Most cleared hole height weights: ', self.format_float_list(self.tetris_ais[highest_scores[0][1]].hole_height_weights, brackets=True))

        new_ais = []
        if avg_most < 1.0:
            [new_ais.append(TetrisAI(self.grid_width, self.grid_height, [], [], [], [])) for i in range(self.population_size)]
        else:
            # produce new generation
            # let half of the most fit of this generation continue on as is
            for i in range(self.population_size // 2):
                new_ais.append(self.tetris_ais[fitness_scores[i][1]].clone())
            # then crossover the most fit until the population size is reached
            while len(new_ais) != self.population_size:
                # randomly select two different parents
                idx1 = randint(0, self.selection_size - 1)
                idx2 = idx1
                while idx2 == idx1:
                    idx2 = randint(0, self.selection_size - 1)
                new_ais.append(self.tetris_ais[highest_scores[idx1][1]].crossover(
                    self.tetris_ais[highest_scores[idx2][1]]))
                new_ais[-1].mutate(self.mutate_rate)

        self.tetris_instances.clear()
        [self.tetris_instances.append(Game(self.grid_width, self.grid_height)) for i in range(self.population_size)]
        self.tetris_ais.clear()
        self.tetris_ais = new_ais
        self.print_starting_generation()

    def update_gui_title(self):
        pygame.display.set_caption(
                f'Tetro | Gen: {self.generation} ' +
                f'Viewing: {self.current_spectating_idx + 1}/{self.population_size} ' +
                ('(LOST)' if self.tetris_instances[self.current_spectating_idx].lost else '(ALIVE)'))

    def print_starting_generation(self):
        print()
        print(f'---- Starting Generation {self.generation} -----')

    def format_float_list(self, float_list, num_decimals=2, delimiter=', ', brackets=False):
        s = delimiter.join([('{:.' + str(num_decimals) + 'f}').format(num) for num in float_list])
        return f'[{s}]' if brackets else s

if __name__ == "__main__":
    app = App()
    app.start()

    #root = tk.Tk()
    #app = Tetro(root)
    #app.mainloop()
