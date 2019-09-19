import math
from time import perf_counter
from tetromino import Tetromino
from random import random, randint
from copy import deepcopy

class TetrisAI:
    def __init__(self, grid_width, grid_height,
        row_filled_weights=[], hole_size_weights=[], column_diff_weights=[]):
        self.grid_width = grid_width
        self.grid_height = grid_height
        # maximum amount of weights for certain weight types
        self.weights_cap = 10
        self.row_filled_weights = row_filled_weights
        self.hole_size_weights = hole_size_weights
        self.column_diff_weights = column_diff_weights
        # generate random weights if not provided
        if len(row_filled_weights) == 0:
            for i in range(grid_width + 1):
                self.row_filled_weights.append(self.random_weight())
        if len(hole_size_weights) == 0:
            for i in range(self.weights_cap):
                self.hole_size_weights.append(self.random_weight())
        if len(column_diff_weights) == 0:
            for i in range(grid_height + 1):
                self.column_diff_weights.append(self.random_weight())

        # test weights that perform ok
        self.row_filled_weights = [1.97, 1.18, 0.32, 0.03, 0.30, 0.38, 0.52, 0.42, 0.17, 0.89, 1.83]
        self.hole_size_weights = [2.05, 1.56, 2.46, 1.44, 0.92, 1.27, 1.04, 1.91, 0.08, 0.52]
        self.column_diff_weights = [0.16, 0.19, 0.40, 0.42, 1.46, 0.73, 0.02, 0.58, 0.48, 0.62, 0.64, 0.43, 0.39, 0.23, 0.88, 0.28, 1.01, 0.26, 0.59, 0.48, 0.21]


    # determine what move should be made given a Tetris instance
    # the type of Tetromino used is the Tetris instance current tetromino
    def compute_move(self, inst):
        tmino_id = inst.current_tmino.data.id
        tmino_size = inst.current_tmino.data.size
        grid = inst.to_boolean_grid()
        heights = self.compute_heightmap(grid)
        best_move = [float('-inf'), None]

        for rotation in inst.tmino_manager.unique_tmino_list[tmino_id - 1]:
            # to compute each possible drop placement, first find the largest value
            # in the heightmap that contains the tetromino at each section of columns
            tmino = Tetromino(inst.tmino_manager.get_tetromino_type(inst.current_tmino.data.id, rotation))
            for i in range(tmino.data.min_x, tmino.data.max_x + 1):
                tmino.x_pos = i
                # find greatest height
                greatest_height = 0
                for j in range(i, i + tmino_size):
                    # check for out of bounds
                    if j >= 0 and j < self.grid_width:
                        if heights[j] > greatest_height:
                            greatest_height = heights[j]
                # we are guaranteed that the tetromino will not have collided with
                # anything before this greatest height value, all that is needed
                # to do now is to find the correct point of contact
                for j in range(max(self.grid_height - greatest_height - tmino_size, tmino.data.min_y), tmino.data.max_y + 1):
                    tmino.y_pos = j
                    if inst.is_colliding(tmino):
                        tmino.y_pos = j - 1
                        break
                if not inst.is_colliding(tmino):
                    # tetromino is now at a possible placement
                    score = self.compute_score(grid, tmino)
                    if score > best_move[0]:
                        best_move = [score, Tetromino(
                            inst.tmino_manager.get_tetromino_type(tmino_id, rotation), tmino.x_pos, tmino.y_pos)]
        return best_move[1]

    # computes a score for the given binary grid arrangement and tetromino placement
    # True should indicate an occupied cell, False should indicate empty cell
    def compute_score(self, grid, tetromino):
        # add the tetromino to the binary grid
        for x in range(tetromino.data.size):
            for y in range(tetromino.data.size):
                grid_x = x + tetromino.x_pos
                grid_y = y + tetromino.y_pos
                # check if the tetromino cell is out of bounds
                if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
                    continue
                # update the grid cell with the tetromino cell
                if tetromino.data.block_data[x][y]:
                    grid[grid_x][grid_y] = True

        # add to score based on how filled the rows are
        score = 0
        for y in range(self.grid_height):
            cells_filled = 0
            for x in range(self.grid_width):
                if grid[x][y]:
                    cells_filled += 1
            score += self.row_filled_weights[cells_filled]

        # subtract from score based on heights of holes
        heights = self.compute_heightmap(grid)
        for x in range(self.grid_width):
            hole_height = 0
            for y in range(self.grid_height - heights[x], self.grid_height):
                if grid[x][y]:
                    if hole_height > 0:
                        score -= self.hole_size_weights[min(hole_height, len(self.hole_size_weights) - 1)]
                        hole_height = 0
                else:
                    hole_height += 1
            if hole_height > 0:
                score -= self.hole_size_weights[min(hole_height, len(self.hole_size_weights) - 1)]

        # subtract from score based on differences in column heights
        for i in range(1, len(heights)):
            score -= self.column_diff_weights[heights[i] - heights[i - 1]]

        # remove this tetromino from the binary grid
        for x in range(tetromino.data.size):
            for y in range(tetromino.data.size):
                grid_x = x + tetromino.x_pos
                grid_y = y + tetromino.y_pos
                if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
                    continue
                if tetromino.data.block_data[x][y]:
                    grid[grid_x][grid_y] = False

        return score

    # finds the heights of the highest occupied cell in each column of a Tetris grid
    def compute_heightmap(self, grid):
        column_heights = []
        for x in range(self.grid_width):
            found = False
            for y in range(self.grid_height):
                if grid[x][y]:
                    column_heights.append(self.grid_height - y)
                    found = True
                    break
            if not found:
                column_heights.append(0)
        return column_heights


    # combines this AI and another by mixing weights
    # returns a new AI with crossovered weights
    def crossover(self, ai):
        crossover_idx = randint(0, len(ai.row_filled_weights))
        new_row_filled_weights = deepcopy(self.row_filled_weights[:crossover_idx] + ai.row_filled_weights[crossover_idx:])
        crossover_idx = randint(0, len(ai.hole_size_weights))
        new_hole_size_weights = deepcopy(self.hole_size_weights[:crossover_idx] + ai.hole_size_weights[crossover_idx:])
        crossover_idx = randint(0, len(ai.column_diff_weights))
        new_column_diff_weights = deepcopy(self.column_diff_weights[:crossover_idx] + ai.column_diff_weights[crossover_idx:])

        return TetrisAI(ai.grid_width, ai.grid_height,
            new_row_filled_weights, new_hole_size_weights, new_column_diff_weights)

    # randomly mutates weights given a mutation rate
    def mutate(self, mutate_rate):
        for i in range(self.grid_width):
            if random() <= mutate_rate:
                self.row_filled_weights[i] = self.random_weight()
        for i in range(self.weights_cap):
            if random() <= mutate_rate:
                self.hole_size_weights[i] = self.random_weight()
        for i in range(self.grid_height):
            if random() <= mutate_rate:
                self.column_diff_weights[i] = self.random_weight()

    # returns a deep copy of this AI
    def clone(self):
        return TetrisAI(
            self.grid_width, self.grid_height,
            deepcopy(self.row_filled_weights),
            deepcopy(self.hole_size_weights),
            deepcopy(self.column_diff_weights))

    # prints a 2d list with nice formatting
    def print_grid(self, grid):
        print('-' * len(grid) * 2)
        for y in range(len(grid[0])):
            print(('').join(['#' if grid[x][y] else '.' for x in range(len(grid))]))

    def random_weight(self):
        # produce along the abs of a standard normal distribution curve using the Box-Muller transform
        return abs(math.sqrt(-2 * math.log(random())) * math.cos(2 * math.pi * random()))
        #return random() * 2 - 1
