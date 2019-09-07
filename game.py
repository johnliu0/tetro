import math
from tetromino import TetrominoManager

# an instance of the Tetris game
class Game:
    def __init__(self, grid_width, grid_height, enable_lookaheads):
        self.grid_width = grid_width
        self.grid_height = grid_height
        # whether or not the game has been lost
        self.lost = False
        self.enable_lookaheads = enable_lookaheads

        # the Tetris grid begins at the top-left corner
        # and can be indexed by grid[x][y]
        self.grid = []
        for x in range(self.grid_width):
            col = [0] * self.grid_height
            self.grid.append(col)

        self.tetromino_manager = TetrominoManager.get_instance()

        self.current_tetromino = self.tetromino_manager.new_tetromino()

    # updates the game logic once; this forces the Tetromino to fall one block
    # if the tetromino is touching the ground
    # then it is placed and a new tetromino is generated
    def update(self):
        if not self.lost:
            # attempt to let tetromino fall downwards one block
            self.current_tetromino.move(y=1)
            # if it is colliding with something, then place it down
            if self.is_colliding(self.current_tetromino):
                self.current_tetromino.move(y=-1)
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
                        fill=self.tetromino_manager.get_tetromino_color(self.grid[x][y]))

        # draw current tetromino
        if not self.lost:
            block_data = self.current_tetromino.get_block_data()
            pos_x = self.current_tetromino.get_pos_x()
            pos_y = self.current_tetromino.get_pos_y()
            for x in range(len(block_data)):
                for y in range(len(block_data[0])):
                    if block_data[x][y]:
                        canvas.create_rectangle(
                            (x + pos_x) * cell_width, (y + pos_y) * cell_width,
                            (x + pos_x + 1) * cell_width, (y + pos_y + 1) * cell_width,
                            fill=self.current_tetromino.get_color())

    # places the tetromino where it is and generate a new one
    def place_tetromino(self):
        block_data = self.current_tetromino.get_block_data()
        pos_x = self.current_tetromino.get_pos_x()
        pos_y = self.current_tetromino.get_pos_y()
        size = self.current_tetromino.get_size()
        for x in range(size):
            for y in range(size):
                if block_data[x][y]:
                    # skip if the cell is out of bounds
                    grid_x = x + pos_x
                    grid_y = y + pos_y
                    if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
                        continue
                    self.grid[grid_x][grid_y] = self.current_tetromino.get_id()

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
                for y in range(current_y, 0, -1):
                    for x in range(self.grid_width):
                        self.grid[x][y] = self.grid[x][y - 1]
            else:
                # otherwise go to next line
                current_y -= 1

        # generate a new tetromino
        self.current_tetromino = self.tetromino_manager.new_tetromino()

        # determine if it is colliding with anything
        if self.is_colliding(self.current_tetromino):
            # move it upwards to try and free it
            while self.is_colliding(self.current_tetromino):
                self.current_tetromino.move(y=-1)
                # check if it has moved out of bounds
                if self.is_colliding(self.current_tetromino, include_grid=False):
                    self.current_tetromino = None
                    self.lost = True
                    break


    # drops the tetromino immediately downwards as far as it can and places it
    def drop_tetromino(self):
        self.current_tetromino.move(y=1)
        while not self.is_colliding(self.current_tetromino):
            self.current_tetromino.move(y=1)
        self.current_tetromino.move(y=-1)
        self.place_tetromino()

    # attempts to move the current tetromino left one block
    def move_left(self):
        self.current_tetromino.move(x=-1)
        if self.is_colliding(self.current_tetromino):
            self.current_tetromino.move(x=1)

    # attempts to move the current tetromino right one block
    def move_right(self):
        self.current_tetromino.move(x=1)
        if self.is_colliding(self.current_tetromino):
            self.current_tetromino.move(x=-1)

    # attempts to move the current tetromino down one block
    def move_down(self):
        self.current_tetromino.move(y=1)
        if self.is_colliding(self.current_tetromino):
            self.current_tetromino.move(y=-1)
            self.place_tetromino()

    # attempts to rotate current tetromino 90 degrees clockwise
    def rotate(self):
        # a rotation in place is attempted first
        self.current_tetromino.rotate()
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
        colliding = self.is_colliding(self.current_tetromino)
        original_x = self.current_tetromino.pos_x

        # attempt to move left
        if colliding:
            max_translation = math.floor(self.current_tetromino.get_size() / 2)
            for i in range(max_translation):
                self.current_tetromino.pos_x -= 1
                if not self.is_colliding(self.current_tetromino):
                    colliding = False
                    break

        # attempt to move right if unsuccessful going left
        if colliding:
            self.current_tetromino.pos_x = original_x
            for i in range(max_translation):
                self.current_tetromino.pos_x += 1
                if not self.is_colliding(self.current_tetromino):
                    colliding = False
                    break

        # check if going right was succesful
        if colliding:
            self.current_tetromino.pos_x = original_x
            # revert rotation
            self.current_tetromino.rotate(False)


    # returns whether or not a tetromino is colliding with the grid
    # it is colliding if it is out of bounds or if it is intersecting
    # with any already placed tetrominoes
    # include_grid may also be passed as false to check only if
    # the tetromino is out of bounds
    def is_colliding(self, tetromino, include_grid=True):
        block_data = self.current_tetromino.get_block_data()
        pos_x = self.current_tetromino.get_pos_x()
        pos_y = self.current_tetromino.get_pos_y()
        for x in range(len(block_data)):
            for y in range(len(block_data[0])):
                if block_data[x][y]:
                    # transform tetromino coordinates to grid coordinates
                    grid_x = x + pos_x
                    grid_y = y + pos_y

                    # check if out of bounds
                    if (grid_x < 0 or grid_y < 0
                        or grid_x >= self.grid_width or grid_y >= self.grid_height):
                        return True

                    # check if intersecting with placed tetrominoes
                    if include_grid and self.grid[grid_x][grid_y] != 0:
                        return True
