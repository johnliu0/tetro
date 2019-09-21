import re as regexp
from copy import deepcopy
from random import randint

# Functionality for handling tetrominoes
class TetrominoManager:
    singleton = None
    def get_instance():
        if TetrominoManager.singleton == None:
            TetrominoManager.singleton = TetrominoManager()
        return TetrominoManager.singleton

    def __init__(self):
        if TetrominoManager.singleton != None:
            raise Exception('Access TetrominoManager using get_instance().')
        self.tmino_list = []
        # describes the rotationally unique tetrominos
        self.unique_tmino_list = []
        self.unique_types = 0

    def random_tetromino(self):
        idx = randint(0, self.unique_types - 1)
        # randomly choose a tetromino with no rotation
        tmino_type = self.tmino_list[idx * 4]
        # place it in the top middle of the grid
        return Tetromino(idx + 1, 0,
            (tmino_type.max_x - tmino_type.min_x) // 2 + tmino_type.min_x, tmino_type.min_y)

    def get_tetromino_color(self, id):
        return self.tmino_list[(id - 1) * 4].color

    # loads tetromino data from the shapes file
    def load_tetrominoes(self, file_path, grid_width, grid_height):
        global unique_types
        with open(file_path, 'r') as f:
            color = ''
            block_data = []
            for line in f:
                line = line.strip()
                # ignore blank lines and comments
                if len(line) == 0 or line[0] == '#':
                    continue
                # start of new tetromino, reset all variables
                if line == 'start':
                    self.unique_types += 1
                    block_data = []
                elif line == 'end':
                    # after finishing reading data about tetromino; process it
                    # use unique_types as an id (acts like a counter)
                    self.process_tetromino(block_data, grid_width, grid_height, self.unique_types, color)
                elif line.startswith('row'):
                    # read row of tetromino block data
                    row_data = regexp.split('(\s+)', line)[2]
                    for i in range(len(row_data)):
                        # initialize block_data if this is the first row specified
                        if len(block_data) == 0:
                            for j in range(len(row_data)):
                                block_data.append([])
                        block_data[i].append(row_data[i] == 'O')
                else:
                    # parse key=value
                    idx_equals = line.find('=')
                    if idx_equals == -1:
                        print(f'Line corrupt: {line}')
                    key = line[:idx_equals]
                    value = line[idx_equals + 1:]
                    if key == 'color':
                        color = tuple([int(token) for token in value.split(',')])

    # given tetromino block data; compute information
    # about rotation and position and add to tetromino_types
    def process_tetromino(self, block_data, grid_width, grid_height, id, color):
        # go through each rotation
        tmino_width = len(block_data)
        tmino_height = len(block_data)
        for i in range(4):
            if i != 0:
                block_data = self.rotate(block_data)
            # find min/max x/y
            min_x, min_y, max_x, max_y = 0, 0, 0, 0
            while not self.out_of_bounds(block_data, min_x - 1, 0, grid_width, grid_height):
                min_x -= 1
            while not self.out_of_bounds(block_data, 0, min_y - 1, grid_width, grid_height):
                min_y -= 1
            while not self.out_of_bounds(block_data, max_x + 1, 0, grid_width, grid_height):
                max_x += 1
            while not self.out_of_bounds(block_data, 0, max_y + 1, grid_width, grid_height):
                max_y += 1
            self.tmino_list.append(TetrominoType(id, block_data, len(block_data), min_x, min_y, max_x, max_y, i, color))
        # now we determine the rotationally symmetrical tetrominoes
        # the AI will use only unique tetrominos to compute scores
        # assume the very first tetromino is rotationally unique
        rotations = [0]
        # compare with the other tetrominos
        for i in range(1, 4):
            unique = True
            for j in range(len(rotations)):
                if not self.rotationally_unique(
                    self.get_tetromino_type(id, i).block_data,

                    self.get_tetromino_type(id, rotations[j]).block_data):
                    unique = False
                    break
            if unique:
                rotations.append(i)
        self.unique_tmino_list.append(rotations)

    # determines if two tetrominos are rotationally unique
    def rotationally_unique(self, block_data1, block_data2):
        size = len(block_data1);
        # find minimally enclosing box for each tetromino
        cols1, rows1, cols2, rows2 = set(), set(), set(), set()
        for x in range(size):
            for y in range(size):
                if block_data1[x][y]:
                    cols1.add(x)
                    rows1.add(y)
                if block_data2[x][y]:
                    cols2.add(x)
                    rows2.add(y)
        width1 = max(cols1) - min(cols1) + 1
        height1 = max(rows1) - min(rows1) + 1
        width2 = max(cols2) - min(cols2) + 1
        height2 = max(rows2) - min(rows2) + 1
        # they must be different if their dimensions differ
        if width1 != width2 or height1 != height2:
            return True

        for i in range(width1):
            for j in range(height1):
                if block_data1[i + min(cols1)][j + min(rows1)] != block_data2[i + min(cols2)][j + min(rows2)]:
                    return True
        return False

    # check if a tetromino is out of bounds at the given coordinates
    def out_of_bounds(self, block_data, x_pos, y_pos, grid_width, grid_height):
        for x in range(len(block_data)):
            for y in range(len(block_data)):
                if block_data[x][y]:
                    # convert local tetromino coordinates to grid coordinates
                    grid_x = x + x_pos
                    grid_y = y + y_pos
                    # check if out of bounds
                    if (grid_x < 0 or grid_y < 0
                        or grid_x >= grid_width
                        or grid_y >= grid_height):
                        return True
        return False

    # performs a 90 degree rotation
    def rotate(self, block_data):
        # we treat the indices of block_data as points in a cartesian space
        # we can then translate the points such that the center of the
        # points which are arranged in a square is the origin of the space
        # then we apply a simple 90 degree rotation by treating the points
        # as complex numbers; multiplying by imaginary number -i performs a 90
        # degree clockwise rotation
        # note that the y-axis in cartesian space points upwards while our
        # matrix y-axis points downwards
        # after simplifying the math, the solution turns out to be quite nice
        new_block_data = []
        for x in range(len(block_data)):
            new_block_data.append([block_data[y][len(block_data) - x - 1] for y in range(len(block_data))])
        return new_block_data

    # prints block data to the console neatly
    def print_block_data(self, block_data):
        for y in range(len(block_data)):
            print(''.join(['@' if block_data[x][y] else '.' for x in range(len(block_data))]))

    def get_tetromino_type(self, id, rotation=0):
        return self.tmino_list[((id - 1) * 4) + (rotation % 4)]

# preprocessed information a tetromino
# provides details about rotation and min/max x/y positions
class TetrominoType:
    def __init__(self, id, block_data, size, min_x, min_y, max_x, max_y, rotation, color):
        self.id = id
        self.block_data = deepcopy(block_data)
        self.size = size
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.rotation = rotation
        self.color = color

# an instance of a tetromino
class Tetromino:
    def __init__(self, id, rotation=0, x_pos=0, y_pos=0):
        # copy over data from the TetrominoType
        self.set_type(id, rotation)
        self.x_pos = x_pos
        self.y_pos = y_pos

    def set_type(self, id, rotation):
        type = TetrominoManager.get_instance().get_tetromino_type(id, rotation)
        self.unique_rotations_list = TetrominoManager.get_instance().unique_tmino_list[id - 1]
        self.block_data = type.block_data
        self.size = type.size
        self.min_x = type.min_x
        self.min_y = type.min_y
        self.max_x = type.max_x
        self.max_y = type.max_y
        self.color = type.color
        self.id = id
        self.rotation = rotation

    def rotate(self, clockwise=True):
        self.set_type(self.id, self.rotation + (1 if clockwise else -1))

    def set_rotation(self, rotation):
        self.set_type(self.id, rotation)
