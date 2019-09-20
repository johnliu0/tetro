import math
import pygame
from tetromino import TetrominoManager

# an instance of the Tetris game
class Tetris:
    def __init__(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        # whether or not the game has been lost yet
        self.lost = False
        self.lines_cleared = 0

        # the Tetris grid begins at the top-left corner
        # and can be indexed by grid[x][y]
        self.grid = []
        for x in range(self.grid_width):
            col = [0] * self.grid_height
            self.grid.append(col)

        self.tmino_manager = TetrominoManager.get_instance()
        self.current_tmino = self.tmino_manager.random_tetromino()
        self.next_tmino = self.tmino_manager.random_tetromino()

    # move current tetromino down one block
    def update(self):
        if self.lost:
            return
        self.current_tmino.y_pos += 1
        # if tetromino is now colliding, then move it back and place it down
        if is_colliding(self.grid, self.current_tmino):
            self.current_tmino.y_pos -= 1
            self.place_tetromino()

    # places the current tetromino down and generates a new one
    def place_tetromino(self):
        # transfer the tetromino data to the grid data
        for x in range(self.current_tmino.size):
            for y in range(self.current_tmino.size):
                if self.current_tmino.block_data[x][y]:
                    # skip if the cell is out of bounds
                    grid_x = x + self.current_tmino.x_pos
                    grid_y = y + self.current_tmino.y_pos
                    if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
                        continue
                    self.grid[grid_x][grid_y] = self.current_tmino.id
        # check for cleared lines
        # start from lowest possible line and go up
        current_y = self.current_tmino.y_pos + self.current_tmino.size - 1
        for i in range(self.current_tmino.size):
            # check if this line is out of bounds
            if current_y >= self.grid_height:
                current_y -= 1
                continue
            # check for line clear
            line_cleared = True
            for x in range(self.grid_width):
                if self.grid[x][current_y] == 0:
                    line_cleared = False
                    break
            # move everything above line down one block if cleared
            if line_cleared:
                self.lines_cleared += 1
                for y in range(current_y, 0, -1):
                    for x in range(self.grid_width):
                        self.grid[x][y] = self.grid[x][y - 1]
            else:
                # otherwise go to next line
                current_y -= 1

        # generate a new tetromino
        self.current_tmino = self.next_tmino
        self.next_tmino = self.tmino_manager.random_tetromino()

        # determine if it is colliding with anything
        if is_colliding(self.grid, self.current_tmino):
            self.current_tmino = None
            self.lost = True

# determines if a given boolean grid and a tetromino are colliding
def is_colliding(grid, tetromino):
    # iterate through each cell in the tetromino itself
    for x in range(tetromino.size):
        for y in range(tetromino.size):
            if tetromino.block_data[x][y]:
                grid_x = x + tetromino.x_pos
                # convert local tetromino coordinates to grid coordinates
                grid_y = y + tetromino.y_pos
                # check if out of bounds
                if (grid_x < 0 or grid_y < 0
                    or grid_x >= len(grid)
                    or grid_y >= len(grid[0])
                    or grid[grid_x][grid_y] != 0):
                    return True
    return False

# returns a boolean representation of the given grid
# where False is an empty cell and True is a filled cell
# note that this creates a new grid in memory
def to_boolean_grid(input_grid):
    grid = []
    for x in range(len(input_grid)):
        grid.append([])
        for y in range(len(input_grid[0])):
            grid[-1].append(input_grid[x][y] != 0)
    return grid
