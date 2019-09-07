# Tetro

Tetris AI using a hybrid genetic neural network algorithm. This library is written in pure Python and requires no additional dependencies.

The input data to the network consists of a binary representation of the Tetris grid, where 0 denotes an empty cell, 1 denotes a filled cell, and additionally, data about what and where the current Tetromino is.

The output data is simply a one-hot encoding of four possible moves: go left one block, go right block, go down one block, drop, and rotate. The main goal is for the AI to imitate how a skilled human would play. Chances are, the AI might even learn an advanced move such as the T-spin.

The fitness function of the AI is a factor of two things: lines cleared and time taken. A weighted average of these two provides the fitness score. We want to maximize the lines that it can clear in the shortest amount of time.

The crossover and mutation occurs on the weights and biases of the neural network.

# TODO
Abstract file parsing (properties.txt, shapes.txt, ai.data) into its own module.
