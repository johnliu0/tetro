import math
from tetromino import Tetromino
from random import random, randint
from copy import deepcopy

class TetrisAI:
    def __init__(self, grid_width, grid_height,
        row_filled_weights=[], hole_size_weights=[], hole_x_pos_weights=[], hole_height_weights=[]):
        self.grid_width = grid_width
        self.grid_height = grid_height
        # maximum amount of weights for certain weight types
        self.weights_cap = 10
        self.row_filled_weights = row_filled_weights
        self.hole_size_weights = hole_size_weights
        self.hole_x_pos_weights = hole_x_pos_weights
        self.hole_height_weights = hole_height_weights

        if len(row_filled_weights) == 0:
            for i in range(grid_width):
                self.row_filled_weights.append(random())
            # extra weight since zero-indexing
            self.row_filled_weights.append(random())
        if len(hole_x_pos_weights) == 0:
            for i in range(grid_width):
                self.hole_x_pos_weights.append(random())
        if len(hole_size_weights) == 0:
            for i in range(self.weights_cap):
                self.hole_size_weights.append(random())
        if len(hole_height_weights) == 0:
            for i in range(self.weights_cap):
                self.hole_height_weights.append(random())


        """if len(self.weights) == 0:
            # scores for how filled a row is
            for i in range(grid_width + 1):
                self.weights.append(random() * 2 - 1)
            # scores for how large a hole is
            # if a hole exceeds this number, then the last weight is used
            for i in range(self.hole_weights_size):
                self.weights.append(random() * 2 - 1)"""

        #self.weights = [0.0, 0.01, 0.04, 0.09, 0.16, 0.25, 0.36, 0.49, 0.64, 0.81, 1.0, 0.3, 0.4, 0.9, 1.6, 2.5, 3.6, 4.9, 6.4, 8.1, 10.0]

    # determine the next move given a Tetris instance
    # returns a tuple in the form (x_pos, y_pos, rotation)
    # representing how the current tetromino in the game should be placed
    def compute_move(self, inst):
        tmino_id = inst.current_tmino.data.id
        grid = inst.to_boolean_grid()

        # keep track of the best move that can be made
        # a list in the format: (score, x_pos, y_pos, rotation)
        best_move = [float('-inf'), 0, 0, None]
        # try each rotation
        for rotation in range(4):
            # initialize the rotated tetromino
            tmino = Tetromino(inst.tmino_manager.get_tetromino_type(tmino_id, rotation))
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
                        score = self.compute_score(grid, tmino)
                        if score > best_move[0]:
                            best_move = [score, tmino.x_pos, tmino.y_pos, tmino.data.rotation]
                        # once we have found a collision, move on to the next column
                        break
        return tuple(best_move[1:])

    # computes a score for the given binary grid arrangement and tetromino placement
    # True should indicate an occupied cell, False should indicate empty cell
    def compute_score(self, grid, tetromino):
        # add the tetromino to the binary grid
        for x in range(tetromino.data.size):
            for y in range(tetromino.data.size):
                if tetromino.data.block_data[x][y]:
                    grid_x = x + tetromino.x_pos
                    grid_y = y + tetromino.y_pos
                    # check if the tetromino cell is out of bounds
                    if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
                        continue
                    # otherwise update the grid cell with the tetromino cell
                    grid[grid_x][grid_y] = True

        # fitness is based on lines cleared and
        # number of cells filled on grid
        # the more cells are filled per row, the higher the score
        # lines cleared are worth exactly 1 point
        score = 0
        for y in range(self.grid_height):
            cells_filled = 0
            for x in range(self.grid_width):
                if grid[x][y] != 0:
                    cells_filled += 1
            score += self.row_filled_weights[cells_filled]

        # compute the number of holes created in grid
        # first initialize a 2d list to keep track of visited cells
        visited = deepcopy(grid)

        # however, do not count cells that can directly see the top row, or the "sky"
        for x in range(self.grid_width):
            for y in range(0, self.grid_height):
                if not visited[x][y]:
                    visited[x][y] = True
                else:
                    break

        # compute heights of holes in each column
        for x in range(self.grid_width):
            hole_height = 0
            for y in range(0, self.grid_height):
                if not visited[x][y]:
                    hole_height += 1
                else:
                    if hole_height > self.weights_cap:
                        score -= self.hole_height_weights[self.weights_cap - 1]
                    elif hole_height > 0:
                        score -= self.hole_height_weights[hole_height - 1]
                    hole_height = 0
            if hole_height > self.weights_cap:
                score -= self.hole_height_weights[self.weights_cap - 1]
            elif hole_height > 0:
                score -= self.hole_height_weights[hole_height - 1]


        # use flood fill to find the sizes of all holes
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                if not visited[x][y]:
                    size = 0
                    mult = 1
                    stack = []
                    stack.append((x, y))
                    while len(stack) != 0:
                        current = stack.pop()
                        mult *= self.hole_x_pos_weights[current[0]]
                        size += 1
                        visited[current[0]][current[1]] = True
                        # check tile to the left
                        if current[0] - 1 >= 0:
                            if not visited[current[0] - 1][current[1]]:
                                stack.append((current[0] - 1, current[1]))
                        # check tile to the right
                        if current[0] + 1 < self.grid_width:
                            if not visited[current[0] + 1][current[1]]:
                                stack.append((current[0] + 1, current[1]))
                        # check tile above
                        if current[1] - 1 >= 0:
                            if not visited[current[0]][current[1] - 1]:
                                stack.append((current[0], current[1] - 1))
                        # check tile below
                        if current[1] + 1 < self.grid_height:
                            if not visited[current[0]][current[1] + 1]:
                                stack.append((current[0], current[1] + 1))
                    # add to score depending on size of the holes
                    if size >= self.weights_cap:
                        score -= self.hole_size_weights[-1] * mult
                    else:
                        score -= self.hole_size_weights[size] * mult

        #for y in range(self.grid_height):
            #print(('').join(['@' if grid[x][y] else '.' for x in range(self.grid_width)]))

        # remove this tetromino from the binary grid
        for x in range(tetromino.data.size):
            for y in range(tetromino.data.size):
                if tetromino.data.block_data[x][y]:
                    grid_x = x + tetromino.x_pos
                    grid_y = y + tetromino.y_pos
                    # check if the tetromino cell is out of bounds
                    if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
                        continue
                    # otherwise
                    grid[grid_x][grid_y] = False
        return score

    # combines this AI and another by mixing weights
    # returns a new AI with crossovered weights
    def crossover(self, ai):
        crossover_idx = randint(0, len(ai.row_filled_weights))
        new_row_filled_weights = deepcopy(self.row_filled_weights[:crossover_idx] + ai.row_filled_weights[crossover_idx:])
        crossover_idx = randint(0, len(ai.hole_size_weights))
        new_hole_size_weights = deepcopy(self.hole_size_weights[:crossover_idx] + ai.hole_size_weights[crossover_idx:])
        crossover_idx = randint(0, len(ai.hole_x_pos_weights))
        new_hole_x_pos_weights = deepcopy(self.hole_x_pos_weights[:crossover_idx] + ai.hole_x_pos_weights[crossover_idx:])
        crossover_idx = randint(0, len(ai.hole_height_weights))
        new_hole_height_weights = deepcopy(self.hole_height_weights[:crossover_idx] + ai.hole_height_weights[crossover_idx:])

        return TetrisAI(ai.grid_width, ai.grid_height,
            new_row_filled_weights, new_hole_size_weights, new_hole_x_pos_weights, new_hole_height_weights)

    def mutate(self, mutate_rate):
        for i in range(self.grid_width):
            if random() <= mutate_rate:
                self.row_filled_weights[i] = random()
            if random() <= mutate_rate:
                self.hole_x_pos_weights[i] = random()
        for i in range(self.weights_cap):
            if random() <= mutate_rate:
                self.hole_size_weights[i] = random()
            if random() <= mutate_rate:
                self.hole_height_weights[i] = random()

def compute_possible_moves(tetris_inst):
    tmino_id = tetris_inst.current_tmino.data.id
    # convert grid to a binary representation
    # where True is an occupied cell and False is an empty cell
    grid = []
    for x in range(tetris_inst.grid_width):
        grid.append([])
        for y in range(tetris_inst.grid_height):
            grid[-1].append(tetris_inst.grid[x][y] != 0)

    # keep track of all possible moves
    moves = []
    # try each rotation
    for rotation in range(4):
        # initialize the rotated tetromino
        tmino = Tetromino(tetris_inst.tmino_manager.get_tetromino_type(tmino_id, rotation))
        # try each possible column
        for x in range(tmino.data.min_x, tmino.data.max_x + 1):
            tmino.x_pos = x
            # find the lowest point that it can drop to
            for y in range(tmino.data.min_y, tmino.data.max_y + 2):
                tmino.y_pos = y
                # if the tetromino is colliding, then the previous move
                # is the furthest it could have dropped
                if tetris_inst.is_colliding(tmino):
                    # however if the tetromino was colliding even at
                    # its min y position, then it is not possible
                    # to make a move in this column
                    if tmino.y_pos == tmino.data.min_y:
                        break
                    tmino.y_pos -= 1

                    moves.append((tmino.x_pos, tmino.y_pos, tmino.data.rotation))
                    # once we have found a collision, move on to the next column
                    break
    return moves

# computes the overall score of a Tetris game
def compute_fitness(inst):
    score = inst.lines_cleared
    """# subtract from score for each hole in grid
    for x in range(len(inst.grid)):
        for y in range(len(inst.grid[0])):
            if inst.grid[x][y] == 0:
                score -= 0.2"""
    return score
