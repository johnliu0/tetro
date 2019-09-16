import math
from random import random, randint
from copy import deepcopy

class TetrisAI:
    def __init__(self, grid_width, grid_height, weights=[]):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.weights = weights
        self.hole_weights_size = 10
        if len(self.weights) == 0:
            """# scores for how filled a row is
            for i in range(grid_width + 1):
                self.weights.append(random())
            # scores for how large a hole is
            # if a hole exceeds this number, then the last weight is used
            for i in range(self.hole_weights_size):
                self.weights.append(random())"""

            self.weights = [0.7112714461917173, 0.2389235992636648, 0.3543599998985706, 0.002794156832754524, 0.0818543349841857, 0.07316713318300061, 0.20932288485496398, 0.21583637249217869, 0.26380968462349674, 0.35201816486172544, 0.9325689569108521, 0.5061789745049843, 0.6853766746288739, 0.3723816930390321, 0.25656705629428456, 0.5602335482545915, 0.7335582661672582, 0.0049787371814449255, 0.25714561216586895, 0.7434473539755115, 0.02387371616911571]

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
            score += self.weights[cells_filled]

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

        # use flood fill to find the sizes of all holes
        hole_sizes = []
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                if not visited[x][y]:
                    size = 0
                    stack = []
                    stack.append((x, y))
                    while len(stack) != 0:
                        current = stack.pop()
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
                    hole_sizes.append(size)

        for size in hole_sizes:
            if size >= self.hole_weights_size:
                score -= self.weights[-1]
            else:
                score -= self.weights[self.grid_width + size]

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
        crossover_idx = randint(0, len(ai.weights))
        new_weights = deepcopy(self.weights[:crossover_idx] + ai.weights[crossover_idx:])
        return TetrisAI(ai.grid_width, ai.grid_height, new_weights)

    def mutate(self, mutate_rate):
        for i in range(len(self.weights)):
            if random() <= mutate_rate:
                self.weights[i] = random()
