# Tetro

## Overview

Tetris AI using a genetic algorithm. This library is written in Python and pygame (3.7.4 and 1.9.6 at the time of writing, respectively). No other libraries are needed. The machine learning logic is written in pure vanilla Python and does not require numpy or any other math libraries.

After letting this run on my computer for a few nights, I discovered that one AI was able to clear over 125,000 lines. This is highest score that I have seen a set of weights clear so far.

## Get Started

Run `python tetro.py`.

Under `data/properties.txt`, you can change the parameters used for the genetic algorithm, including population size, selection size, and mutation rate.

## Sreenshot

![Screenshot of Tetro](/data/screenshot.png)

## How the genetic algorithm works

After a good deal of experimentation with various machine learning models, I found that writing a weight-based AI whose weights could be trained through a genetic algorithm worked best. Under `ai.py` is where you will find all the AI logic. For each move, the possible placements (from only vertically dropping it; i.e. this algorithm does not take into account pieces that have to be tucked under another one, so no T-spins sorry!) are calculated. For each placement, a score is assigned to it based on how it fits with the existing grid. Three heuristics form the basis of the algorithm.

1. How filled the rows are: `row_filled_weights`
2. How high each 'hole' in the grid is: `hole_height_weights`
3. The difference in height from one column to another: `column_diff_weights`

Using a set of weights that described these three heuristics seemed to work best.

The row filled weights simply assigns a score for each row in the grid. If a row was filled,
the last weight would be taken. If a row had only 3 filled cells, then the 4th weight would be taken. The 1st weight belongs to the scenario where a row has no cells whatsoever. The row fillings are to be maximized.

A hole in the grid is defined as any successive vertical cells that are under a filled cell. It may or may not be blocked; but the algorithm does not check for placements that require more than one horizontal translation to attain. Essentially, if the cell cannot directly see the top row of the grid, then it is a hole. The number of holes is to be minimized.

The difference in heights of successive columns is exactly as described. Since we want the existing cells to be relatively uniform in height, this number is minimized.

The game generates many instances of the genetic algorithm which control their own Tetris instance. At the end of each generation, when all Tetris instances have lost, the weights in the AIs are cross-overed and mutated to create a new generation of Tetris AIs.

## File structure
- `tetro.py`: Main file.
- `ai.py`: AI logic.
- `tetris.py`: Tetris game implementation.
- `tetromino.py`: Tetromino logic.
- `data/properties.txt`: Specifications for game properties.
- `data/weights.txt`: Information about the highest scoring AI of each generation.
