import re as regexp
import copy
from random import randint

class Tetromino:
    def __init__(self, id, size, block_data, color, startx, starty):
        self.id = id
        self.size = size
        self.block_data = copy.deepcopy(block_data)
        self.color = color
        self.pos_x = startx
        self.pos_y = starty

    # returns the id of this tetromino
    # tetrominos of the same kind (block_data, color, etc.) share the same id
    def get_id(self):
        return self.id

    def get_size(self):
        return self.size

    def get_block_data(self):
        return self.block_data

    def get_color(self):
        return self.color

    def get_pos_x(self):
        return self.pos_x

    def get_pos_y(self):
        return self.pos_y

    # performs a 90 degree rotation
    def rotate(self, clockwise=True):
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
        for x in range(self.size):
            col = []
            for y in range(self.size):
                col.append(
                    self.block_data[y][self.size - x - 1]
                    if clockwise else
                    self.block_data[self.size - y - 1][x])
            new_block_data.append(col)
        self.block_data = new_block_data



    # moves this tetromino by a specified amount
    def move(self, x=0, y=0):
        self.pos_x += x
        self.pos_y += y

# handles generation of new tetrominoes
class TetrominoManager:
    singleton = None
    def get_instance():
        if TetrominoManager.singleton == None:
            TetrominoManager.singleton = TetrominoManager()
        return TetrominoManager.singleton

    def __init__(self):
        if TetrominoManager.singleton != None:
            raise Exception("Access TetrominoManager using get_instance()")

        self.tetromino_list = []

    # loads tetromino data from the shapes file
    def load_tetrominoes(self, file_path):
        with open(file_path, 'r') as f:
            current_tetromino = None
            # each tetromino gets a unique id (index of tetromino data in tetromino_list)
            # ids begin at 1 since the Tetris grid will use 0 as an empty space
            unique_id = 1

            for line in f:
                line = line.strip()

                # ignore blank lines and comments
                if len(line) == 0 or line[0] == '#':
                    continue

                # generate a new tetromino template
                if line == "start":
                    current_tetromino = {
                        "unique_id": unique_id,
                        "block_data": []
                    }
                    unique_id += 1
                elif line == "end":
                    # end the current tetromino template
                    self.tetromino_list.append(current_tetromino)
                elif line.startswith('row'):
                    # read tetromino block data
                    row_data = regexp.split("(\s+)", line)[2]
                    for i in range(current_tetromino["size"]):
                        current_tetromino["block_data"][i].append(row_data[i] == "O")
                else:
                    # parse key=value
                    idx_equals = line.find('=')
                    if idx_equals == -1:
                        print(f"Line corrupt: {line}")
                    key = line[:idx_equals]
                    value = line[idx_equals + 1:]

                    if key == "color":
                        current_tetromino["color"] = value
                    elif key == "size":
                        # initialize tetromino data
                        current_tetromino["size"] = int(value)
                        for i in range(int(value)):
                            current_tetromino["block_data"].append([])

    # generates a randomly selected tetromino
    def new_tetromino(self, startx=0, starty=0) -> Tetromino:
        # randomly select a tetromino dataset
        idx = randint(0, len(self.tetromino_list) - 1)
        return Tetromino(
            self.tetromino_list[idx]["unique_id"],
            self.tetromino_list[idx]["size"],
            self.tetromino_list[idx]["block_data"],
            self.tetromino_list[idx]["color"],
            startx,
            starty
        )

    # returns the color of the tetromino with a given id
    def get_tetromino_color(self, id):
        return self.tetromino_list[id - 1]["color"]
