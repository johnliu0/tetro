import math
import copy
from random import random, randint

# a neural network for playing Tetris
class NeuralNetwork:
    def __init__(self, weights, biases, layer_sizes):
        self.biases = biases
        self.weights = weights
        self.layer_sizes = layer_sizes

    # returns a list of size 5 containing scores of the four moves:
    # go left, go right, go down, drop, rotate
    # input is a binary representation of the grid, and tetromino data
    def activate(self, grid):
        output = []
        layer_output = []
        for i in range(self.layer_sizes[1]):
            weighted_avg = 0
            for x in range(len(grid)):
                for y in range(len(grid[0])):
                    weighted_avg += (self.weights[0][x * len(grid[0]) + y]
                    [i] *
                    grid[x][y])
            layer_output.append(relu(weighted_avg + self.biases[0][i]))
        # iterate through the rest of the hidden layers
        for i in range(len(self.layer_sizes) - 3):
            next_output = []
            for j in range(self.layer_sizes[i + 2]):
                weighted_avg = 0
                for k in range(len(layer_output)):
                    weighted_avg += self.weights[i + 1][k][j] * layer_output[k]
                next_output.append(relu(weighted_avg + self.biases[i + 1][j]))
            layer_output = next_output
        # finally produce an output
        final_output = 0
        for i in range(self.layer_sizes[-1]):
            for j in range(len(layer_output)):
                final_output += self.weights[-1][j][i] * layer_output[j]

        return final_output

def generate_neural_network(grid_width, grid_height, hidden_layers=[5]):
    layer_sizes = []
    output_layer_size = 1
    # initalize weights in range [-1, 1]
    # weights array is three-dimensional
    # weights[i][j][k] represents the weight from the jth node of the ith layer
    # to the kth node of the (i+1)th layer
    weights = []
    # initialize biases in range [-1, 1]
    biases = []

    # input layer
    input_size = grid_width * grid_height
    layer_sizes.append(input_size)
    layer_sizes.extend(hidden_layers)
    # output layer with 5 moves
    layer_sizes.append(output_layer_size)

    # input layer
    weights.append([])
    for i in range(input_size):
        weights[0].append([])
        for j in range(hidden_layers[0] if len(hidden_layers) > 0 else output_layer_size):
            weights[0][i].append(random_standard_normal())

    # hidden layers
    for i in range(len(hidden_layers) - 1):
        weights.append([])
        for j in range(hidden_layers[i]):
            weights[i + 1].append([])
            for k in range(hidden_layers[i + 1]):
                weights[i + 1][j].append(random_standard_normal())
    for i in range(len(hidden_layers)):
        biases.append([])
        for j in range(hidden_layers[i]):
            biases[i].append(random_standard_normal())

    # output layers
    weights.append([])
    if len(hidden_layers) > 0:
        for i in range(hidden_layers[-1]):
            weights[-1].append([])
            for j in range(layer_sizes[-1]):
                weights[-1][i].append(random_standard_normal())
    biases.append([])
    for i in range(layer_sizes[-1]):
        biases[-1].append(random_standard_normal())

    return NeuralNetwork(weights, biases, layer_sizes)


def compute_fitness(tetris_inst):
    # fitness is based on lines cleared and
    # number of cells filled on grid
    # the more cells are filled per row, the higher the score
    # lines cleared are worth exactly 1 point
    grid_width = tetris_inst.grid_width
    score = 0
    score_factor = 1 / (grid_width * grid_width)
    for y in range(tetris_inst.grid_height):
        cells_filled = 0
        for x in range(grid_width):
            if tetris_inst.grid[x][y] != 0:
                cells_filled += 1
        score += score_factor * cells_filled * cells_filled
    return tetris_inst.lines_cleared + score

# combines two neural networks by mixing their weights and biases
def crossover(network1, network2):
    weights = []
    biases = []
    layer_sizes = network1.layer_sizes
    for i in range(len(network1.weights)):
        weights.append([])
        for j in range(len(network1.weights[i])):
            weights[-1].append([])
            crossover_idx = randint(0, len(network1.weights[i][j]))
            weights[-1][-1] = copy.deepcopy(
                network1.weights[i][j][:crossover_idx]
                + network2.weights[i][j][crossover_idx:])

    for i in range(len(network1.biases)):
        crossover_idx = randint(0, len(network1.biases[i]))
        biases.append(copy.deepcopy(
            network1.biases[i][:crossover_idx]
            + network2.biases[i][crossover_idx:]))

    return NeuralNetwork(weights, biases, copy.deepcopy(network1.layer_sizes))

def mutate(network, mutate_rate):
    for i in range(len(network.weights)):
        for j in range(len(network.weights[i])):
            if random() <= mutate_rate:
                for k in range(len(network.weights[i][j])):
                    network.weights[i][j][k] = random_standard_normal()

    for i in range(len(network.biases)):
        for j in range(len(network.biases[i])):
            if random() <= mutate_rate:
                network.biases[i][j] = random_standard_normal()

# rectified linear function
def relu(x):
    return 0 if x <= 0 else x

# sigmoid function; range is [0, 1]
def sigmoid(x):
    return 1 / (1 + math.exp(-x))

# normal distribution/probability density function, mean = 0, standard deviation = 1
def random_standard_normal():
    # this uses the Box-Muller transform for generating
    # standard normally distributed random numbers
    return math.sqrt(-2 * math.log(random())) * math.cos(2 * math.pi * random())
