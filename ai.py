import math
from time import perf_counter
from tetris import is_colliding
from tetromino import Tetromino
from random import random, randint
from copy import deepcopy

class TetrisAI:
    def __init__(self, grid_width, grid_height,
        row_filled_weights=[], hole_height_weights=[], column_diff_weights=[]):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.row_filled_weights = row_filled_weights
        self.hole_height_weights = hole_height_weights
        self.column_diff_weights = column_diff_weights
        # number of weights to use for hole height and column diff heuristics
        # note that row filled weights uses grid_width + 1 weights
        self.hole_height_cap = 5
        self.column_diff_cap = 5
        # generate random weights if not provided
        if len(row_filled_weights) == 0:
            for i in range(grid_width + 1):
                self.row_filled_weights.append(self.random_weight())
        if len(hole_height_weights) == 0:
            for i in range(self.hole_height_cap):
                self.hole_height_weights.append(self.random_weight())
        if len(column_diff_weights) == 0:
            for i in range(self.column_diff_cap):
                self.column_diff_weights.append(self.random_weight())

        # test weights that perform ok
        #self.row_filled_weights = [2.12, 1.50, 1.04, 0.50, 0.10, 0.32, 0.18, 0.28, 0.18, 0.27, 1.24]
        #self.hole_height_weights = [1.47, 1.78, 1.43, 2.03, 1.40]
        #self.column_diff_weights = [0.65, 0.67, 0.83, 0.88, 1.03]

    # determine what move should be made given a Tetris instance
    # the type of Tetromino used is the Tetris instance current tetromino
    def compute_move(self, inst):
        best_move = ()
        grid = self.to_boolean_grid(inst.grid)
        # compute moves available with the current tetromino
        first_moves = self.compute_moves_available(grid, inst.current_tmino)
        scores = []
        # for every move with the current tetromino,
        # compute moves available with the next tetromino
        for move1 in first_moves:
            tmino1 = Tetromino(inst.current_tmino.id, move1[0], move1[1], move1[2])
            self.add_to_grid(grid, tmino1)
            score = self.compute_score(grid)
            scores.append(score)
            self.remove_from_grid(grid, tmino1)
            """highest_score = float('-inf')
            # compute possible moves for the next tetromino
            second_moves = self.compute_moves_available(grid, inst.next_tmino)
            for move2 in second_moves:
                tmino2 = Tetromino(inst.next_tmino.id, move2[0], move2[1], move2[2])
                self.add_to_grid(grid, tmino2)
                score = self.compute_score(grid)
                if score > highest_score:
                    highest_score = score
                self.remove_from_grid(grid, tmino2)
            self.remove_from_grid(grid, tmino1)
            # use the average second move score as the score for a first move
            scores.append(highest_score)"""
        highest_idx = 0
        for i in range(1, len(scores)):
            if scores[i] > scores[highest_idx]:
                highest_idx = i
        best_move = first_moves[highest_idx]
        return Tetromino(inst.current_tmino.id, best_move[0], best_move[1], best_move[2])

    # computes all possible drop placements that can be made
    def compute_moves_available(self, grid, tetromino):
        heights = self.compute_heightmap(grid)
        possible_moves = []
        # consider each rotation
        for rotation in tetromino.unique_rotations_list:
            # to compute each possible drop placement, first find the largest value
            # in the heightmap that contains the tetromino at each section of columns
            tmino = Tetromino(tetromino.id, rotation)
            for i in range(tetromino.min_x, tetromino.max_x + 1):
                tmino.x_pos = i
                # find greatest height
                greatest_height = 0
                for j in range(i, i + tetromino.size):
                    # check for out of bounds
                    if j >= 0 and j < len(grid):
                        if heights[j] > greatest_height:
                            greatest_height = heights[j]
                # we are guaranteed that the tetromino will not have collided with
                # anything before this greatest height value, all that is needed
                # to do now is to find the correct point of contact
                for j in range(max(len(grid[0]) - greatest_height - tetromino.size, tetromino.min_y), tetromino.max_y + 1):
                    tmino.y_pos = j
                    if is_colliding(grid, tmino):
                        tmino.y_pos = j - 1
                        break
                if not is_colliding(grid, tmino):
                    # tetromino is now at a possible placement
                    possible_moves.append((rotation, tmino.x_pos, tmino.y_pos))
        return possible_moves

    # computes a score for the given binary grid arrangement
    # True should indicate an occupied cell, False should indicate empty cell
    def compute_score(self, grid):
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
                        score -= self.hole_height_weights[min(hole_height, self.hole_height_cap) - 1]
                        hole_height = 0
                else:
                    hole_height += 1
            if hole_height > 0:
                score -= self.hole_height_weights[min(hole_height, self.hole_height_cap - 1)]

        # subtract from score based on differences in column heights
        for i in range(1, len(heights)):
            score -= self.column_diff_weights[min(abs(heights[i] - heights[i - 1]), self.column_diff_cap - 1)]
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

    # adds a tetromino to a grid
    def add_to_grid(self, grid, tmino):
        for x in range(tmino.size):
            for y in range(tmino.size):
                grid_x = x + tmino.x_pos
                grid_y = y + tmino.y_pos
                # check if the tmino cell is out of bounds
                if grid_x < 0 or grid_x >= len(grid) or grid_y < 0 or grid_y >= len(grid[0]):
                    continue
                # update the grid cell with the tmino cell
                if tmino.block_data[x][y]:
                    grid[grid_x][grid_y] = True

    # removes a tetromino from a grid
    def remove_from_grid(self, grid, tmino):
        for x in range(tmino.size):
            for y in range(tmino.size):
                grid_x = x + tmino.x_pos
                grid_y = y + tmino.y_pos
                if grid_x < 0 or grid_x >= len(grid) or grid_y < 0 or grid_y >= len(grid[0]):
                    continue
                if tmino.block_data[x][y]:
                    grid[grid_x][grid_y] = False

    # combines this AI and another by mixing weights
    # returns a new AI with crossovered weights
    def crossover(self, ai):
        crossover_idx = randint(0, len(ai.row_filled_weights))
        new_row_filled_weights = deepcopy(self.row_filled_weights[:crossover_idx] + ai.row_filled_weights[crossover_idx:])
        crossover_idx = randint(0, len(ai.hole_height_weights))
        new_hole_height_weights = deepcopy(self.hole_height_weights[:crossover_idx] + ai.hole_height_weights[crossover_idx:])
        crossover_idx = randint(0, len(ai.column_diff_weights))
        new_column_diff_weights = deepcopy(self.column_diff_weights[:crossover_idx] + ai.column_diff_weights[crossover_idx:])

        return TetrisAI(ai.grid_width, ai.grid_height,
            new_row_filled_weights, new_hole_height_weights, new_column_diff_weights)

    # randomly mutates weights given a mutation rate
    def mutate(self, mutate_rate):
        for i in range(self.grid_width):
            if random() <= mutate_rate:
                self.row_filled_weights[i] = self.random_weight()
        for i in range(self.hole_height_cap):
            if random() <= mutate_rate:
                self.hole_height_weights[i] = self.random_weight()
        for i in range(self.column_diff_cap):
            if random() <= mutate_rate:
                self.column_diff_weights[i] = self.random_weight()

    def random_weight(self):
        # produce along the abs of a standard normal distribution curve using the Box-Muller transform
        return abs(math.sqrt(-2 * math.log(random())) * math.cos(2 * math.pi * random()))
        #return random() * 2 - 1

    # returns a deep copy of this AI
    def clone(self):
        return TetrisAI(
            self.grid_width, self.grid_height,
            deepcopy(self.row_filled_weights),
            deepcopy(self.hole_height_weights),
            deepcopy(self.column_diff_weights))

    # returns a boolean representation of the given grid
    # where False is an empty cell and True is a filled cell
    # note that this creates a new grid in memory
    def to_boolean_grid(self, grid):
        b_grid = []
        for x in range(len(grid)):
            b_grid.append([])
            for y in range(len(grid[0])):
                b_grid[-1].append(grid[x][y] != 0)
        return b_grid

    # prints a 2d list with nice formatting
    def print_grid(self, grid):
        print('-' * len(grid) * 2)
        for y in range(len(grid[0])):
            print(('').join(['#' if grid[x][y] else '.' for x in range(len(grid))]))
