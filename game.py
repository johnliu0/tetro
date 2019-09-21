import math
import pygame
from random import randint
from tetromino import TetrominoManager

# an instance of the Tetris game
class Game:
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
        # generate random sequence of tetrominos
        # the sequence will contain all types of tetrominos (excluding rotation)
        # when all the tetrominos in the sequence have been used, another
        # sequence will be generated. this this is to ensure that the distribution is fair
        self.tmino_seq = self.generate_tetromino_seq()
        self.current_tmino = tmino_seq[-1]
        self.tmino_seq.pop()
        self.next_tmino = tmino_seq[-1]
        self.tmino_seq.pop()

    # move current tetromino down one block
    def update(self):
        if self.lost:
            return
        self.current_tmino.y_pos += 1
        # if tetromino is now colliding, then move it back and place it down
        if self.is_colliding(self.current_tmino):
            self.current_tmino.y_pos -= 1
            self.place_tetromino()

    def render(self, surface, font, cell_width):
        # draw grid
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                # draw the cell if it is non empty
                if self.grid[x][y] != 0:
                    pygame.draw.rect(
                        surface,
                        self.tmino_manager.get_tetromino_color(self.grid[x][y]),
                        (x * cell_width, y * cell_width, cell_width - 1, cell_width - 1))
        # draw a divider line
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (self.grid_width * cell_width, 0, 1, self.grid_height * cell_width))

        if not self.lost:
            # draw current tetromino
            block_data = self.current_tmino.block_data
            pos_x = self.current_tmino.x_pos
            pos_y = self.current_tmino.y_pos
            for x in range(len(block_data)):
                for y in range(len(block_data[0])):
                    if block_data[x][y]:
                        pygame.draw.rect(
                            surface,
                            self.current_tmino.color,
                            ((x + pos_x) * cell_width, (y + pos_y) * cell_width,
                            cell_width - 1, cell_width - 1))
            # draw next tetromino
            text = font.render('Next piece: ', True, (255, 255, 255))
            textRect = text.get_rect()
            textRect.topleft = ((self.grid_width + 1) * cell_width, cell_width)
            surface.blit(text, textRect)
            block_data = self.next_tmino.block_data
            pos_x = self.grid_width + 1
            pos_y = 3
            for x in range(len(block_data)):
                for y in range(len(block_data[0])):
                    if block_data[x][y]:
                        pygame.draw.rect(
                            surface,
                            self.next_tmino.color,
                            ((x + pos_x) * cell_width, (y + pos_y) * cell_width,
                            cell_width - 1, cell_width - 1))


    # attempts to move the tetromino left
    def move_left(self):
        self.current_tmino.x_pos -= 1
        if self.is_colliding(self.current_tmino):
            self.current_tmino.x_pos += 1

    # attempts to move the tetromino right
    def move_right(self):
        self.current_tmino.x_pos += 1
        if self.is_colliding(self.current_tmino):
            self.current_tmino.x_pos -= 1

    # attempts to move the tetromino down
    def move_down(self):
        self.current_tmino.y_pos += 1
        if self.is_colliding(self.current_tmino):
            self.current_tmino.y_pos -= 1
            self.place_tetromino()

    # attemps to rotate the tetromino
    def rotate(self):
        # a rotation in place is attempted first
        self.current_tmino.rotate()
        # if it is colliding, then move the tetromino left or right
        # and try to find a non-colliding spot
        # a maximum of tetromino.get_size() / 2 blocks can be tried left or right
        # this is done because some blocks may simply be pressed up against
        # a wall or other pieces and have room to move to the side
        # a common case where this happens is when the I tetromino
        # is pressed up against the wall
        # the tetromino will be attempted to move left first
        # this is a rather arbitrary decision since there may be a free spot
        # to both the left and the right; in this case, the left spot
        # would take precedence
        colliding = self.is_colliding(self.current_tmino)
        original_x = self.current_tmino.x_pos

        # attempt to move left
        if colliding:
            max_translation = self.current_tmino.data.size // 2
            for i in range(max_translation):
                self.current_tmino.x_pos -= 1
                if not self.is_colliding(self.current_tmino):
                    colliding = False
                    break

        # attempt to move right if unsuccessful going left
        if colliding:
            self.current_tmino.x_pos = original_x
            for i in range(max_translation):
                self.current_tmino.x_pos += 1
                if not self.is_colliding(self.current_tmino):
                    colliding = False
                    break

        # check if going right was successful
        if colliding:
            self.current_tmino.x_pos = original_x
            # revert rotation
            self.current_tmino.rotate(False)

    # drops the tetromino immediately downwards as far as possible and places it
    def drop(self):
        while not self.is_colliding(self.current_tmino):
            self.current_tmino.y_pos += 1
        self.current_tmino.y_pos -= 1
        self.place_tetromino()


    # check if a tetromino is colliding with any existing cells or out of bounds
    def is_colliding(self, tetromino):
        # iterate through each cell in the tetromino itself
        for x in range(tetromino.data.size):
            for y in range(tetromino.data.size):
                if tetromino.data.block_data[x][y]:
                    grid_x = x + tetromino.x_pos
                    # convert local tetromino coordinates to grid coordinates
                    grid_y = y + tetromino.y_pos
                    # check if out of bounds
                    if (grid_x < 0 or grid_y < 0
                        or grid_x >= self.grid_width
                        or grid_y >= self.grid_height
                        or self.grid[grid_x][grid_y] != 0):
                        return True
        return False

    # places the current tetromino down and generates a new one
    def place_tetromino(self):
        # transfer the tetromino data to the grid data
        for x in range(self.current_tmino.data.size):
            for y in range(self.current_tmino.data.size):
                if self.current_tmino.data.block_data[x][y]:
                    # skip if the cell is out of bounds
                    grid_x = x + self.current_tmino.x_pos
                    grid_y = y + self.current_tmino.y_pos
                    if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
                        continue
                    self.grid[grid_x][grid_y] = self.current_tmino.data.id
        # check for cleared lines
        # start from lowest possible line and go up
        current_y = self.current_tmino.y_pos + self.current_tmino.data.size - 1
        for i in range(self.current_tmino.data.size):
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
        if len(self.tmino_seq) == 0:
            self.tmino_seq = self.generate_tetromino_seq()
            self.next_tmino = self.tmino_seq[-1]
            tmino_seq.pop()

        # determine if it is colliding with anything
        if self.is_colliding(self.current_tmino):
            self.current_tmino = None
            self.lost = True

    def generate_tetromino_seq(self):
        seq = []
        id_list = [i for i in range(1, self.tmino_manager.unique_types + 1)]
        # randomly pull ids from the list and put it into the sequence
        while len(id_list) != 0:
            rand_idx = randint(0, len(id_list) - 1)
            id = id_list[rand_idx]
            id_list.pop(rand_idx)
            tmino = Tetromino(id)
            tmino.x_pos = (tmino.max_x - tmino.min_x) // 2
            tmino.y_pos = tmino.min_y
            seq.append(tmino)
        return seq
