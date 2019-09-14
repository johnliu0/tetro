import math
from random import random

# a neural network for playing Tetris
class NeuralNetwork:
    # initializes with a specified number of hidden layers
    # and how many neurons each layer has
    # the min and max x and y represent how negative and how positive the
    # positions of the tetrominos can be
    # the output layer is fixed to four outputs that represent a score
    # from 0 to 1 of how good the move is; the highest will be taken
    # hidden_layers describes how many
    def __init__(self, num_type_tetrominoes, grid_width, grid_height,
        min_pos_x, min_pos_y, max_pos_x, max_pos_y, hidden_layers=[128, 128, 128]):
        self.num_type_t = num_type_tetrominoes
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.min_pos_x = min_pos_x
        self.min_pos_y = min_pos_y
        self.max_pos_x = max_pos_x
        self.max_pos_y = max_pos_y
        self.layer_sizes = []
        self.output_layer_size = 5
        # initalize weights in range [-1, 1]
        # the weights is three-dimensional
        # weights[i][j][k] represents the weight from the jth node of the ith layer
        # to the kth node of the (i+1)th layer
        self.weights = []
        # input layer consists of:
        # representation of the grid, coordinate and type of current tetromino
        # the grid representation is binary, with 0 denoting an empty cell
        # the coordinates are integers representing the x, y position of the tetromino
        # the number of types of tetrominoes is integer as well
        # the three integers will be linearly normalized down to [-1, 1]
        # when activating the network
        input_size = grid_width * grid_height + 3
        self.layer_sizes.append(input_size)
        self.layer_sizes.extend(hidden_layers)
        # output layer
        self.layer_sizes.append(self.output_layer_size)
        self.weights.append([])
        for i in range(input_size):
            self.weights[0].append([])
            for j in range(hidden_layers[0] if len(hidden_layers) > 0 else self.output_layer_size):
                self.weights[0][i].append(random() * 2 - 1)

        # hidden layers
        for i in range(len(hidden_layers) - 1):
            self.weights.append([])
            for j in range(hidden_layers[i]):
                self.weights[i + 1].append([])
                for k in range(hidden_layers[i + 1]):
                    self.weights[i + 1][j].append(random() * 2 - 1)

        # output layers
        self.weights.append([])
        if len(hidden_layers) > 0:
            for i in range(hidden_layers[-1]):
                self.weights[-1].append([])
                for j in range(self.layer_sizes[-1]):
                    self.weights[-1][i].append(random() * 2 - 1)

    # returns a list of size 5 containing scores of the four moves:
    # go left, go right, go down, drop, rotate
    # input is a binary representation of the grid, and tetromino data
    def activate(self, grid, tetromino_x, tetromino_y, tetromino_type):
        output = []
        layer_output = []
        for i in range(self.layer_sizes[1]):
            weighted_avg = 0
            for x in range(self.grid_width):
                for y in range(self.grid_height):
                    weighted_avg += self.weights[0][x * self.grid_height + y][i] * grid[x][y]
            # x position
            weighted_avg += (self.weights[0][self.grid_width * self.grid_height][i]
                * self.lin_norm(tetromino_x, self.min_pos_x, self.max_pos_x))
            # y position
            weighted_avg += (self.weights[0][self.grid_width * self.grid_height + 1][i]
                * self.lin_norm(tetromino_y, self.min_pos_y, self.max_pos_y))
            # type of tetromino
            weighted_avg += (self.weights[0][self.grid_width * self.grid_height + 2][i]
                * self.lin_norm(tetromino_x, 1, self.num_type_t))
            layer_output.append(self.relu(weighted_avg))
        #print(layer_output)

        # iterate through the rest of the hidden layers
        for i in range(len(self.layer_sizes) - 3):
            next_output = []
            for j in range(self.layer_sizes[i + 2]):
                weighted_avg = 0
                for k in range(len(layer_output)):
                    weighted_avg += self.weights[i + 1][k][j] * layer_output[k]
                next_output.append(self.relu(weighted_avg))
            layer_output = next_output
            print(layer_output)

        final_output = []
        for j in range(self.layer_sizes[-1]):
            weighted_avg = 0
            for k in range(len(layer_output)):
                weighted_avg += self.weights[-1][k][j] * layer_output[k]
            final_output.append(weighted_avg)

        print(final_output)
        return final_output

    # rectified linear function
    def relu(self, x):
        return 0 if x <= 0 else x

    # sigmoid function; range is [0, 1]
    def sigmoid(self, x):
        return 1 / (1 + math.exp(-x))

    # linearly normalizes down to [-1, 1]
    def lin_norm(self, x, lower, upper):
        if x <= lower:
            return lower
        if x >= upper:
            return upper
        # first restrict to [0, 1]
        # then expand to [-1, 1]
        return ((x - lower) / (upper - lower)) * 2 - 1


def compute_fitness(tetris_inst):
    return tetris_inst.score

def crossover(network1, network2):
    pass

def mutate(network):
    pass
