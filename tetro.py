import sys
import math
import pygame
from copy import deepcopy
from random import random, randint
from game import Game
from ai import TetrisAI
from tetromino import TetrominoManager, Tetromino

class Tetro:
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
        self.cell_width = 40
        # active Tetris games and neural networks
        self.tetris_instances = []
        self.tetris_ais = []
        # index of the tetris game that is currently being rendered to screen
        self.current_spectating_idx = 0

        self.load_properties()
        self.init_pygame()

        # how long to sleep in ms per frame
        self.sleep_times = [1, 5, 10, 25, 100, 300, 1000, 2000, 5000, 10000]
        self.sleep_time_idx = 2

        self.tmino_manager = TetrominoManager.get_instance()
        self.tmino_manager.load_tetrominoes('data/shapes.txt', self.grid_width, self.grid_height)
        self.game_running = False
        self.game_paused = False

    def start(self):
        self.game_running = True
        self.game_loop()

    def init_pygame(self):
        pygame.init()
        self.pygame_surface = pygame.display.set_mode(
            ((self.grid_width + 6) * self.cell_width,
            self.grid_height * self.cell_width))
        self.pygame_font = pygame.font.Font(pygame.font.get_default_font(), 32)

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
                elif key == 'crossover_rate':
                    self.crossover_rate = float(value)
                elif key == 'mutate_rate':
                    self.mutate_rate = float(value)

    def game_loop(self):
        self.generate_random_games(self.population_size)
        self.print_starting_generation()
        game_clock = pygame.time.Clock()
        fps_timer, fps_counter = 0, 0
        while self.game_running:
            self.handle_input()
            if not self.game_paused:
                self.update()
            self.render()
            self.update_gui_title()

            # keep track of average FPS over the last 10 seconds
            fps_counter += 1
            fps_timer += game_clock.get_time()
            if fps_timer >= 10000:
                #print(f'Average FPS: {fps_counter / 5}')
                fps_counter = 0
                fps_timer -= 10000

            # sleep so your CPU doesn't blow up!
            pygame.time.wait(500)
            game_clock.tick()

    def update(self):
        # update all tetris instances
        all_lost = True
        for inst, ai in zip(self.tetris_instances, self.tetris_ais):
            inst.update()
            if inst.lost:
                continue
            all_lost = False
            inst.current_tmino = ai.compute_move(inst)

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
            self.pygame_surface, self.pygame_font, self.cell_width)
        pygame.display.flip()

    # handles keyboard and window input
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_j: # view previous game
                    self.current_spectating_idx -= 1
                    self.current_spectating_idx %= len(self.tetris_instances)
                elif event.key == pygame.K_k: # view next game
                    self.current_spectating_idx += 1
                    self.current_spectating_idx %= len(self.tetris_instances)
                elif event.key == pygame.K_p: # pause
                    self.game_paused = not self.game_paused
                elif event.key == pygame.K_o: # view game with highest score
                    highest_idx = -1
                    highest_score = -1
                    for i, inst in enumerate(self.tetris_instances):
                        if not inst.lost and inst.lines_cleared > highest_score:
                            highest_idx = i
                            highest_score = inst.lines_cleared
                    if highest_idx != -1:
                        self.current_spectating_idx = i
                        self.print_current_spectating_stats()
                elif event.key == pygame.K_v: # view stats about current spectating game
                    self.print_current_spectating_stats()
                elif event.key == pygame.K_g: # increase sleep time
                    self.sleep_time_idx += 1
                    self.sleep_time_idx %= len(self.sleep_times)
                    print(f'Changed sleep time to: {self.sleep_times[self.sleep_time_idx]}')
                elif event.key == pygame.K_h: # decrease sleep time
                    self.sleep_time_idx -= 1
                    self.sleep_time_idx %= len(self.sleep_times)
                    print(f'Changed sleep time to: {self.sleep_times[self.sleep_time_idx]}')

    def generate_random_games(self, num=1):
        self.tetris_instances.clear()
        self.tetris_ais.clear()
        for i in range(num):
            self.tetris_instances.append(Game(self.grid_width, self.grid_height))
            self.tetris_ais.append(TetrisAI(self.grid_width, self.grid_height, [], [], []))

    def next_generation(self):
        self.generation += 1
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

        new_ais = []
        if avg_most < 1 / self.selection_size:
            [new_ais.append(TetrisAI(self.grid_width, self.grid_height, [], [], [])) for i in range(self.population_size)]
        else:
            # produce new generation
            # let half of the most fit of this generation continue on as is
            for i in range(self.population_size // 2):
                new_ais.append(self.tetris_ais[fitness_scores[i][1]].clone())
            # then crossover the most fit until the population size is reached
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

    def print_current_spectating_stats(self):
        print()
        print(f'Currently spectatating game: {self.current_spectating_idx + 1}/{self.population_size}')
        print(f'Lines cleared: {self.tetris_instances[self.current_spectating_idx].lines_cleared}')

    def format_float_list(self, float_list, num_decimals=2, delimiter=', ', brackets=False):
        s = delimiter.join([('{:.' + str(num_decimals) + 'f}').format(num) for num in float_list])
        return f'[{s}]' if brackets else s

# for color printing to console
class Colors:
    RED = '\033[1;31m'
    BLUE = '\033[1;34m'
    CYAN = '\033[1;36m'
    GREEN = '\033[0;32m'
    RESET = '\033[0;0m'
    BOLD = '\033[;1m'
    REVERSE = '\033[;7m'
    ENDC = '\033[0m'

if __name__ == '__main__':
    tetro = Tetro()
    tetro.start()
