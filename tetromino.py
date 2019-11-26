import re as regexp
from copy import deepcopy
from random import randint

# list of TetrominoType objects that describes all the possible tetrominos
# and all possible rotations
tmino_list = []

# list of lists pointing to the indices of all rotationally unique tetrominos
unique_tmino_list = []

# number of unique types of tetrominos by shape
unique_types = 0

def load(file_path, grid_width, grid_height):
    """Loads tetromino data from the provided configuration file.

    Args:
        file_path: Location to shapes.txt file.
        grid_width: Number of columns in Tetris grid.
        grid_height: Number of rows in Tetris grid.
    """

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
                unique_types += 1
                block_data = []
            elif line == 'end':
                # after finishing reading data about tetromino; process it
                # use unique_types as an id (acts like a counter)
                process_tetromino(block_data, grid_width, grid_height, unique_types, color)
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
def process_tetromino(block_data, grid_width, grid_height, id, color):
    """Processes data about a Tetromino and stores it into tmino_list and
    unique_tmino_list.

    This precomputed data is used to allow the Tetris instance and AI to become
    much faster.

    Args:
        block_data: A square 2d array describing a Tetromino.
        grid_width: Number of columns in Tetris grid.
        grid_height: Number of rows in Tetris grid.
    """

    global tmino_list;
    global unique_tmino_list;

    # go through each of the four possible rotations and find minimum and maximum
    # x and y coordinates, add these to the tmino_list
    tmino_width = len(block_data)
    tmino_height = len(block_data)
    for i in range(4):
        if i != 0:
            block_data = rotate(block_data)
        # find min/max x/y
        min_x, min_y, max_x, max_y = 0, 0, 0, 0
        while not out_of_bounds(block_data, min_x - 1, 0, grid_width, grid_height):
            min_x -= 1
        while not out_of_bounds(block_data, 0, min_y - 1, grid_width, grid_height):
            min_y -= 1
        while not out_of_bounds(block_data, max_x + 1, 0, grid_width, grid_height):
            max_x += 1
        while not out_of_bounds(block_data, 0, max_y + 1, grid_width, grid_height):
            max_y += 1
        tmino_list.append(TetrominoType(id, block_data, len(block_data), min_x, min_y, max_x, max_y, i, color))

    # determine the rotationally symmetrical tetrominoes
    # use the block_data given as the first rotational variant
    rotations = [0]
    # try the three other rotations possible
    for i in range(1, 4):
        unique = True
        # compare the current rotation with all of existing rotationally unique
        # tetrominos, if it does not already exist, then it must be unique
        for j in range(len(rotations)):
            if not rotationally_unique(
                get_tetromino_type(id, i).block_data,
                get_tetromino_type(id, rotations[j]).block_data):
                unique = False
                break
        if unique:
            rotations.append(i)
    unique_tmino_list.append(rotations)

def rotationally_unique(block_data1, block_data2):
    """Determines if two tetrominos are rotationally unique."""

    size = len(block_data1);
    # find minimally enclosing box for each tetromino
    # essentially filtering all rows and columns that don't contain anything
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

    # check if any cell differs
    for i in range(width1):
        for j in range(height1):
            if block_data1[i + min(cols1)][j + min(rows1)] != block_data2[i + min(cols2)][j + min(rows2)]:
                return True
    return False

def out_of_bounds(block_data, x_pos, y_pos, grid_width, grid_height):
    """Determines if a tetromino is out of bounds at the given coordinates."""

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

def rotate(block_data):
    """Performs a 90 degree rotation clockwise.

    We treat the indices of block_data as points in a cartesian space. Then, we
    translate the points such that the center of the block_data is at the
    origin. Next, we apply a 90 degree clockwise rotation by treating the points
    as complex numbers, and multiplying by -i. Note that the y-axis in cartesian
    space points upwards while our block_data 2d array y-axis points downwards.
    After simplifying the math, the solution turns out to be quite nice.

    The above is a needlessly complicated byproduct of my (albeit limited)
    knowledge of linear algebra.
    """

    new_block_data = []
    for x in range(len(block_data)):
        new_block_data.append([block_data[y][len(block_data) - x - 1] for y in range(len(block_data))])
    return new_block_data

def get_tetromino_type(id, rotation=0):
    """Gets the TetrominoType object that corresponds to a given tetromino id
    and rotation."""

    return tmino_list[((id - 1) * 4) + (rotation % 4)]

def random_tetromino():
    """Generates a random tetromino in its first rotation state."""

    # randomly choose a tetromino
    idx = randint(0, unique_types - 1)
    tmino_type = tmino_list[idx * 4]
    # place it in the top middle of the grid
    return Tetromino(idx + 1, 0,
        (tmino_type.max_x - tmino_type.min_x) // 2 + tmino_type.min_x, tmino_type.min_y)

def get_tetromino_color(id):
    """Returns the color of the tetromino associated with a given id."""

    return tmino_list[(id - 1) * 4].color

def get_largest_tetromino_size():
    """Returns the size of the largest tetromino."""

    largest_idx = 0
    for i in range(1, unique_types):
        if tmino_list[i * 4].size > tmino_list[largest_idx * 4].size:
            largest_idx = i
    return tmino_list[largest_idx * 4].size


# prints block data to the console neatly
def print_block_data(block_data):
    for y in range(len(block_data)):
        print(''.join(['@' if block_data[x][y] else '.' for x in range(len(block_data))]))

class TetrominoType:
    """Preprocessed information about a tetromino."""

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

class Tetromino:
    def __init__(self, id, rotation=0, x_pos=0, y_pos=0):
        self.set_type(id, rotation)
        self.x_pos = x_pos
        self.y_pos = y_pos

    def set_type(self, id, rotation):
        type = get_tetromino_type(id, rotation)
        self.unique_rotations_list = unique_tmino_list[id - 1]
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
