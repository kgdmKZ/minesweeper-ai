# Author: Andrew Zadravec
#
# This class contains methods to run Minesweeper games and print time and move
# count statistics for an algorithm that selects game moves and is implemented
# via analyzeBoard() and determineMove(). By default, a MinesweeperAI instance will
# play a game by repeatedly selecting a random move, but subclasses should
# implement more clever versions of analyzeBoard() and determineMove().
#

from minesweeper import Minesweeper
import time
from random import randint

class MinesweeperAI(object):
    def __init__(self, game_config=()):
        self.game = Minesweeper(True, game_config)


    # Small functions that may be useful as arguments to getSurroundingSquares()
    # and for other purposes. Some of these methods follow the recommendation
    # that full implementations of MinesweeperAI represent mines as '*'
    # characters and known safe, unrevealed squares as 'S' internally.
    @staticmethod
    def isMine(row, col, value):
        return value == '*'

    @staticmethod
    def isUnknown(row, col, value):
        return value == '?'

    @staticmethod
    def isNum(row, col, value):
        return value.isdigit()

    @staticmethod
    def isSafe(row, col, value):
        return v in (' ', 'S')

    @staticmethod
    def justPosition(row, col, value):
        return (row, col)

    @staticmethod
    def distance(sq1, sq2):
        return max(abs(sq1[0]-sq2[0]), abs(sq1[1]-sq2[1]))

    @staticmethod
    def asIs(x):
        return x

    @staticmethod
    def asSet(x):
        return {*x}

    @staticmethod
    def asCount(generator):
        return sum(1 for elt in generator)

    @staticmethod
    def seenFn(seen):
        return (lambda r, c, v: (r, c) in seen)

    @staticmethod
    def notCondFn(condFn):
        return (lambda *rcv: not condFn(*rcv))

    @staticmethod
    def composeCond(condFn1, condFn2):
        return (lambda *rcv: condFn1(*rcv) and condFn2(*rcv))


    # Override this to change how the board is printed after each move
    def printBoard(self):
        self.game.printBoard()

    # Resets instance variables to run a new Minesweeper game
    def nextGame(self, game_config=()):
        self.game.reset(game_config)

    # Examines the game board in the Minesweeper instance and updates the
    # data stored in this MinesweeperAI instance after a game move
    def analyzeBoard(self):
        # nothing to update (subclasses should usually have some instance
        # variables tracking useful information about the current state of the
        # game to update by overriding this method)
        pass

    # Determines the next game move to make and returns a row, col tuple
    def determineMove(self):
        while 1:
            row = randint(0, self.game.rows-1)
            col = randint(0, self.game.cols-1)

            if self.game.board[row][col] == '?':
                return (row, col)

    # Play one game with the specified numbers of rows, columns, and mines
    def playGame(self, game_config=()):
        # reset the game with input configuration
        self.nextGame(game_config)

        moves = 0
        start = time.time()

        self.printBoard()

        while 1:
            move = self.determineMove()
            self.game.revealSquare(*move, False)

            moves += 1
            if self.game.inProgress:
                self.analyzeBoard()
                self.printBoard()
            else:
                break

        end = time.time()
        duration = end-start

        print("\nCompletion time: \n\t%f seconds" % duration)
        print("Number of moves: \n\t%d\n" % moves)

        return self.game.isWon(), moves

    def getRandomConfig(self):
        rows = randint(1, 100)

        cols = randint(1, 100)

        if rows*cols == 1:
            return self.getRandomConfig()

        mines = randint(1, rows*cols-1)

        return rows, cols, mines

    # Plays n games where game parameters are either random each time or fixed
    # at the same rows, cols, mines values as given
    #
    # If provided, game_config should be a tuple of (rows, columns, mines) in
    # the games that will be instantiated. It is ignored unless randomly is set
    # to False (by default, this method randomly configures each game).
    #
    # If randomly is False and game_config is not provided, each game will use
    # the last configured game settings over again (so callers should only
    # create this condition when the current game instance has such settings
    # and it is desirable to reuse them).
    def playGames(self, n, randomly=True, game_config=()):
        wins = 0
        moves = 0
        start = time.time()

        if not randomly and not game_config:
            game_config = (
                self.game.rows, self.game.cols, self.game.mines
            )

        for i in range(n):
            print("Starting game %d\n" % (i+1))

            if randomly:
                game_config = self.getRandomConfig()

            print("Rows: %d" % game_config[0])
            print("Columns: %d" % game_config[1])
            print("Mines: %d\n" % game_config[2])

            won, gameMoves = self.playGame(game_config)

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

    # Takes a tuple containing the row and column numbers of a square in the
    # game board and returns the string stored in the board, or None if the
    # row and/or col numbers are out of bounds
    def safeGet(self, row, col):
        return self.game.safeGet((row, col))

    # A helper function to get a set of surrounding squares in the game board
    # given the row and column of a square. The set contains tuples where the
    # first value is a tuple of row and column numbers and the second is the
    # string stored in the board.
    #
    # This method is designed to facilitate a wide range of use cases:
    #
    # The immediately surrounding squares can be filtered based on whether each
    # square makes conditionFn return a true value (by default it always does).
    #
    # conditionFn and transformSqFn both take the following arguments: row
    # number, column number, and value at the relevant square.
    #
    # transformSqFn allows the caller to decide on a different value derived
    # from a square's value and position to be returned instead of the default,
    # which is to return a (row, column, value) tuple.
    #
    # transformGenFn takes the generator for all the surrounding square values
    # (that meet conditionFn and as transformed by transformSqFn) and transforms
    # it into some other return value. The most common use is to return
    # something else aside from a generator, like a set, list, etc. The default
    # function if this argument is not provided will return a list of each
    # generated element.
    def getSurroundingSquares(self, row, col,
        conditionFn=(lambda r, c, v: 1),
        transformSqFn=(lambda r, c, v: (r, c, v)),
        transformGenFn=(lambda generator: [*generator])
    ):
        return transformGenFn(
            transformSqFn(i, j, self.safeGet(i, j))
                for i in range(row-1, row+2)
                for j in range(col-1, col+2)
                if self.safeGet(i, j) is not None
                    and not (i == row and j == col)
                    and conditionFn(i, j, self.safeGet(i, j))
        )
