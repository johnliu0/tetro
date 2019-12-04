import sys
import math
import pygame
from time import time_ns
from datetime import datetime
from copy import deepcopy
from random import random, randint
from tetris import Tetris
from ai import TetrisAI
import tetromino

class Tetro:
    """Entry point for Tetro.

    Controls all Tetris instances and corresponding AIs. Manages the population
    in each generation of AIs. Handles Pygame window.
    """

    def __init__(self):
        # basic Tetris and genetic algorithm properties
        self.grid_width = 0
        self.grid_height = 0
        self.population_size = 0
        self.selection_size = 0
        self.mutate_rate = 0
        self.generation = 0

        # size of cell in pixels (for rendering)
        self.cell_width = 40

        # active Tetris games and neural networks
        self.tetris_instances = []
        self.tetris_ais = []

        # index of the tetris game that is currently being rendered to screen
        self.current_spectating_idx = 0

        self.load_properties()
        tetromino.load('data/shapes.txt', self.grid_width, self.grid_height)
        self.init_pygame()

        # list of ai delays that can be toggled through
        self.ai_delay_list = [0, 1, 5, 10, 25, 100, 250, 500, 1000, 1500, 2000, 2500, 3000]
        self.current_ai_delay_idx = 1
        self.average_fps = 0

        # path to save the highest scoring AI weights to
        self.output_weight_path = 'data/weights.txt'
        self.highest_score = 0
        self.next_move_outline = True

        self.game_running = False
        self.game_paused = False

    def start(self):
        print(
            '\n\nHey, thanks for checking out Tetro.\n'
            'Press H while focused in the game to bring up available commands\n'
            'If you find any issues or bugs please report them on my GitHub repo at:\n'
            'https://github.com/johnliu4/tetro.git. Thanks!\n'
            'Have fun with Tetro. :)\n')
        self.game_running = True
        self.game_loop()

    # init pygame and any gui related components
    def init_pygame(self):
        pygame.init()
        # dimensions of the Tetris grid itself
        tetris_width = self.grid_width * self.cell_width
        tetris_height = self.grid_height * self.cell_width
        # additional gui space is determined by the largest tetromino that can fit
        # this is since the gui will show the next tetromino piece
        extra_width = (tetromino.get_largest_tetromino_size() + 2) * self.cell_width
        self.pygame_surface = pygame.display.set_mode((tetris_width + extra_width, tetris_height))

    def handle_start_button_press(self):
        if self.game_paused:
            self.game_paused = False
            self.start_button.set_text('Pause')
        else:
            self.game_paused = True
            self.start_button.set_text('Start')

    # loads game options from the properties file
    def load_properties(self):
        with open('data/properties.txt', 'r') as f:
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
                elif key == 'mutate_rate':
                    self.mutate_rate = float(value)

    def game_loop(self):
        self.generate_random_games(self.population_size)
        self.print_starting_generation()
        game_clock = pygame.time.Clock()
        fps_timer, fps_counter = 0, 0

        ai_clock = 0
        while self.game_running:
            ai_clock += game_clock.get_time()
            self.handle_input()

            # update game only when enough time has passed
            ai_clock += game_clock.get_time()
            if ai_clock >= self.ai_delay_list[self.current_ai_delay_idx]:
                if not self.game_paused:
                    self.update()
                ai_clock -= self.ai_delay_list[self.current_ai_delay_idx]

            self.render()
            self.update_gui_title()

            # keep track of average FPS over the last 10 seconds
            fps_counter += 1
            fps_timer += game_clock.get_time()
            if fps_timer >= 1000:
                self.average_fps = fps_counter
                fps_counter = 0
                fps_timer -= 1000

            # run as fact as you can!
            pygame.time.wait(1)
            game_clock.tick()

    def update(self):
        # update all Tetris instances that have not lost yet
        all_lost = True
        for inst, ai in zip(self.tetris_instances, self.tetris_ais):
            inst.update()
            if inst.lost:
                continue
            all_lost = False
            inst.next_move = ai.compute_move(inst)

        # start next generation if all Tetris instances have lost
        if all_lost:
            self.next_generation()

    def render(self):
        self.pygame_surface.fill((0, 0, 0))
        self.tetris_instances[self.current_spectating_idx].render(self.pygame_surface, self.next_move_outline)
        pygame.display.flip()

    # handles keyboard and window input
    def handle_input(self):
        """Handles all keyboard input from the user."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.game_running = False

                elif event.key == pygame.K_p: # pause
                    self.game_paused = not self.game_paused
                    if self.game_paused:
                        print('Paused AI')
                    else:
                        print('Resumed AI')

                elif event.key == pygame.K_j: # view previous game
                    self.current_spectating_idx -= 1
                    self.current_spectating_idx %= len(self.tetris_instances)

                elif event.key == pygame.K_k: # view next game
                    self.current_spectating_idx += 1
                    self.current_spectating_idx %= len(self.tetris_instances)


                elif event.key == pygame.K_o: # view game with highest score
                    highest_idx = -1
                    highest_score = -1
                    for i, inst in enumerate(self.tetris_instances):
                        if not inst.lost and (inst.lines_cleared > highest_score):
                            highest_idx = i
                            highest_score = inst.lines_cleared
                    if highest_idx != -1:
                        self.current_spectating_idx = highest_idx
                        print(f'Switched to instance {highest_idx + 1} with {self.tetris_instances[highest_idx].lines_cleared} line clears')

                elif event.key == pygame.K_v: # view stats about current generation
                    self.print_current_generation_stats()

                elif event.key == pygame.K_y: # view stats about the current spectated game
                    self.print_current_game_stats()

                elif event.key == pygame.K_u: # slow down ai
                    if self.current_ai_delay_idx == len(self.ai_delay_list) - 1:
                        print(f'Already at the slowest delay: {self.ai_delay_list[self.current_ai_delay_idx]}ms')
                    else:
                        self.current_ai_delay_idx += 1
                        print(f'Slowed down AI delay to: {self.ai_delay_list[self.current_ai_delay_idx]}ms')

                elif event.key == pygame.K_i: # speed up ai
                    if self.current_ai_delay_idx == 0:
                        print('Already at no delay')
                    else:
                        self.current_ai_delay_idx -= 1
                        if self.current_ai_delay_idx == 0:
                            print ('Turned off AI delay')
                        else:
                            print(f'Slowed down AI delay to: {self.ai_delay_list[self.current_ai_delay_idx]}ms')

                elif event.key == pygame.K_g: # toggle next move outline:
                    self.next_move_outline = not self.next_move_outline
                    if self.next_move_outline:
                        print('Turned on next move outline')
                    else:
                        print('Turned off next move outline')

                elif event.key == pygame.K_h: # display help for all commands
                    print(
                        '\n----- Help -----\n\n'
                        '(h)\n'
                        '\tDisplays this! View help for all available commands.\n'
                        '(p)\n'
                        '\tPause the game.\n'
                        '(q)\n'
                        '\tQuit the game.\n'
                        '(j)\n'
                        '\tView the previous Tetris instance.\n'
                        '(k)\n'
                        '\tView the next Tetris instance.\n'
                        '(o)\n'
                        '\tSwitch to the live Tetris instance with the most lines cleared.\n'
                        '(v)\n'
                        '\tDisplay stats about the current generation.\n'
                        '(y)\n'
                        '\tDisplays stats about the current instance.\n'
                        '(u)\n'
                        '\tSlow down AI delay.\n'
                        '(i)\n'
                        '\tSpeed up AI delay.\n'
                        '(g)\n'
                        '\tToggle next move outline.\n')

    def generate_random_games(self, num=1):
        """Generates a completely new set of Tetris instanes and AIs with randomized weights."""

        self.tetris_instances.clear()
        self.tetris_ais.clear()
        for i in range(num):
            self.tetris_instances.append(Tetris(self.grid_width, self.grid_height, self.cell_width))
            self.tetris_ais.append(TetrisAI(self.grid_width, self.grid_height, [], [], []))

    def next_generation(self):
        """Ends the current generation and produces the next generation of AIs."""

        self.generation += 1
        # get fitness scores and sort
        fitness_scores = [(inst.lines_cleared, i) for i, inst in enumerate(self.tetris_instances)]
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
        print('Most cleared hole height weights: ', self.format_float_list(self.tetris_ais[highest_scores[0][1]].hole_height_weights, brackets=True))
        print('Most cleared column diff weights: ', self.format_float_list(self.tetris_ais[highest_scores[0][1]].column_diff_weights, brackets=True))

        # save the weights of the highest scoring AI
        with open('data/weights.txt', 'a') as f:
            f.write('\n')
            f.write(str(datetime.now()) + '\n')
            f.write(f'Generation: {self.generation - 1} | Instance: {self.current_spectating_idx + 1}/{self.population_size}\n')
            f.write(f'Lines cleared: {fitness_scores[0][0]}\n')
            f.write(self.format_float_list(self.tetris_ais[highest_scores[0][1]].row_filled_weights, brackets=True) + '\n')
            f.write(self.format_float_list(self.tetris_ais[highest_scores[0][1]].hole_height_weights, brackets=True) + '\n')
            f.write(self.format_float_list(self.tetris_ais[highest_scores[0][1]].column_diff_weights, brackets=True) + '\n')

        # prepare next generation
        new_ais = []
        # create completely new AIs if the average was too low
        if avg_most <= 0.1:
            [new_ais.append(TetrisAI(self.grid_width, self.grid_height, [], [], [])) for i in range(self.population_size)]
        else:
            # produce new generation
            # let the upper third of the most fit of this generation continue on as is
            for i in range(self.population_size // 2):
                new_ais.append(self.tetris_ais[fitness_scores[i][1]].clone())
            # then crossover until the population size is reached
            while len(new_ais) != self.population_size:
                # randomly select two different parents
                idx1 = randint(0, len(highest_scores) - 1)
                idx2 = idx1
                while idx2 == idx1:
                    idx2 = randint(0, len(highest_scores) - 1)
                new_ais.append(self.tetris_ais[highest_scores[idx1][1]].crossover(
                    self.tetris_ais[highest_scores[idx2][1]]))
                new_ais[-1].mutate(self.mutate_rate)

        self.tetris_instances.clear()
        [self.tetris_instances.append(Tetris(self.grid_width, self.grid_height, self.cell_width)) for i in range(self.population_size)]
        self.tetris_ais.clear()
        self.tetris_ais = new_ais
        self.print_starting_generation()

    def update_gui_title(self):
        """Updates the Pygame's window title."""

        pygame.display.set_caption(
                f'Tetro | Gen: {self.generation} ' +
                f'Viewing: {self.current_spectating_idx + 1}/{self.population_size} ' +
                ('(Lost)' if self.tetris_instances[self.current_spectating_idx].lost else '(Alive)') +
                f' | FPS: {self.average_fps}')

    def print_starting_generation(self):
        """Prints a header for the new generation."""

        print(f'\n----- Starting Generation {self.generation} -----')

    # returns a list of tuples containing the Tetris instance index and its score in sorted order
    def print_current_generation_stats(self):
        """Gets information about the current generation of Tetris AIs.

        Returns:
            A list of tuples containing the Tetris instance index and its score
            in sorted order, example: [(3, 40), (2, 30), ... (9, 10)].
        """

        # get fitness scores and sort
        fitness_scores = [(inst.lines_cleared, '' if inst.lost else ' (Alive)') for i, inst in enumerate(self.tetris_instances)]
        print('\nLines cleared: ', (', ').join([f'{elem[0]}{elem[1]}' for elem in fitness_scores]))

    def print_current_game_stats(self):
        """Prints to console the status of the currently spectated game."""

        print(f'\nYou are currently viewing game: {self.current_spectating_idx + 1}')
        print('Row filled weights: ', self.format_float_list(self.tetris_ais[self.current_spectating_idx].row_filled_weights, brackets=True))
        print('Hole height weights: ', self.format_float_list(self.tetris_ais[self.current_spectating_idx].hole_height_weights, brackets=True))
        print('Column diff weights: ', self.format_float_list(self.tetris_ais[self.current_spectating_idx].column_diff_weights, brackets=True))

    def format_float_list(self, float_list, num_decimals=2, delimiter=', ', brackets=False):
        """Returns a nicely formatted list of floats."""

        s = delimiter.join([('{:.' + str(num_decimals) + 'f}').format(num) for num in float_list])
        return f'[{s}]' if brackets else s

if __name__ == '__main__':
    tetro = Tetro()
    tetro.start()
