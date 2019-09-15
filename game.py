import math
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
        self.current_tmino = self.tmino_manager.random_tetromino()

    # move current tetromino down one block
    def update(self):
        if self.lost:
            return

        self.current_tmino.y_pos += 1
        # if tetromino is now colliding, then move it back and place it down
        if self.is_colliding(self.current_tmino):
            self.current_tmino.y_pos -= 1
            self.place_tetromino()

    def render(self, canvas, cell_width):
        # draw background
        canvas.create_rectangle(0, 0,
            cell_width * self.grid_width, cell_width * self.grid_height, fill="black")

        # draw grid
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                # draw the cell if it is non empty
                if self.grid[x][y] != 0:
                    canvas.create_rectangle(
                        x * cell_width, y * cell_width,
                        (x + 1) * cell_width, (y + 1) * cell_width,
                        fill=self.tmino_manager.get_tetromino_color(self.grid[x][y]))

        # draw current tetromino
        if not self.lost:
            block_data = self.current_tmino.data.block_data
            pos_x = self.current_tmino.x_pos
            pos_y = self.current_tmino.y_pos
            for x in range(len(block_data)):
                for y in range(len(block_data[0])):
                    if block_data[x][y]:
                        canvas.create_rectangle(
                            (x + pos_x) * cell_width, (y + pos_y) * cell_width,
                            (x + pos_x + 1) * cell_width, (y + pos_y + 1) * cell_width,
                            fill=self.current_tmino.data.color)

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
                self.current_tmino.pos_x -= 1
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

        # check if going right was succesful
        if colliding:
            self.current_tmino.x_pos = original_x
            # revert rotation
            self.current_tmino.rotate()

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
        current_y = self.grid_height - 1
        while current_y >= 0:
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
        self.current_tmino = self.tmino_manager.random_tetromino()

        # determine if it is colliding with anything
        if self.is_colliding(self.current_tmino):
            self.current_tmino = None
            self.lost = True
