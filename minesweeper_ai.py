# Author: Andrew Zadravec
#
# This class contains methods to run Minesweeper games and print time and move
# count statistics for an algorithm that selects game moves and is implemented
# via analyzeBoard() and makeMove(). By default, a MinesweeperAI instance will
# play a game by repeatedly selecting a random move out of the move options
# that would reveal at least one new square, but subclasses should
# reimplement some functionality to change this behavior.
#

from minesweeper import Minesweeper
import time
from random import randint

class MinesweeperAI(object):
    def __init__(self):
        self.game = Minesweeper(True, rows=0, cols=0, mines=0)
        self.augmentedBoard = None
        self.moves = 0

    # Examines the game board in the Minesweeper instance and changes the
    # augmented board in response
    def analyzeBoard(self):
        self.augmentedBoard = self.game.board

    # Uses a newly-modified augmented board to determine the next game move
    def makeMove(self):
        choseValidReveal = False
        while not choseValidReveal:
            row = randint(0, self.game.rows-1)
            col = randint(0, self.game.cols-1)
            if self.augmentedBoard[row][col] == '?':
                self.game.revealSquare(row, col)
                choseValidReveal = True

    # Play one game with the specified numbers of rows, columns, and mines
    def playGame(self, rows, cols, mines):
        # reset the game with input configuration
        self.game.reset(rows, cols, mines)
        moves = 0
        start = time.time()

        while self.game.inProgress:
            self.analyzeBoard()
            self.makeMove()
            moves += 1

        end = time.time()
        duration = end-start

        print("\nCompletion time: \n\t%f seconds" % duration)
        print("Number of moves: \n\t%d\n" % moves)

        return self.game.isWon(), moves

    def getRandomConfig(self):
        rows = randint(1, 100)

        if rows == 1:
            cols = randint(2, 100)
        else:
            cols = randint(1, 100)

        mines = randint(1, rows*cols-1)

        return rows, cols, mines

    # Play n games where game parameters are either random or
    # fixed at the same rows, cols, mines values for each game
    def playGames(self, n, randomly=True, **fixedConfig):
        wins = 0
        moves = 0
        start = time.time()

        if not randomly:
            rows = fixedConfig['rows']
            cols = fixedConfig['cols']
            mines = fixedConfig['mines']

        for i in xrange(n):
            print("Starting game %d\n" % (i+1))

            if randomly:
                rows, cols, mines = self.getRandomConfig()

            print("Rows: %d" % rows)
            print("Columns: %d" % cols)
            print("Mines: %d\n" % mines)

            won, gameMoves = self.playGame(rows, cols, mines)
            if won:
                wins += 1
            moves += gameMoves


        end = time.time()
        duration = end-start

        print("\nGames completed")
        print("Wins: %d" % wins)
        print("Losses: %d" % (n-wins))
        print("Win Percentage: %f" % ((float(wins)/n)*100))
        print("Total time: %f seconds" % duration)
        print("Total moves: %d\n" % moves)
