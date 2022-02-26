# Author: Andrew Zadravec
#
# A simple Minesweeper Solver

from minesweeper_ai import MinesweeperAI
from random import randint

class MinesweeperSolver(MinesweeperAI):
    def __init__(self, game_config=()):
        super(MinesweeperSolver, self).__init__(game_config)
        self.resetSolverState()

    def resetSolverState(self):
        # set of 2-element tuples for the rows and columns of squares on the
        # board that have not been revealed but that are known not to have a
        # mine because it can be inferred from the current board state
        self.safeUnrevealed = set()

        # set of 2-element tuples for the rows and columns of each square on
        # the board that is known to have a mine
        self.mines = set()

        # row and column of the most recent move that was made
        (self.row, self.col) = (None, None)

    # When starting a new game, reset the variables tracking where the mines and
    # guaranteed safe spaces on the board are, as well as the most recent game
    # move row and col. Also reset the board for the game itself.
    def nextGame(self, game_config=()):
        self.resetSolverState()
        super(MinesweeperSolver, self).nextGame(game_config)

    # use MinesweeperAI safeGet() method but change some values from the board
    # in cases where mines or safeUnrevealed contain them
    def safeGet(self, rowCol):
        if rowCol in self.mines:
            return '*'
        if rowCol in self.safeUnrevealed:
            return 'S'

        return super(MinesweeperSolver, self).safeGet(rowCol)

    # Look at squares surrounding numbered squares to determine
    # by elimination whether the unknown squares must be mines
    # or safe spaces that are guaranteed not to have mines
    def markSafeAndMines(self):
        numberedSquares = [
            (i, j)
            for i in range(self.game.rows)
            for j in range(self.game.cols)
            if self.safeGet((i, j)).isdigit()
        ]

        for (i, j) in numberedSquares:
            number = int(self.safeGet((i, j)))
            surrounding = self.getSurroundingSquares(i, j)
            unknowns = [sq[0] for sq in surrounding if sq[1] == '?']
            mines = [sq[0] for sq in surrounding if sq[1] == '*']
            numRemainingMines = number - len(mines)
            # the unknown squares must be the missing mines
            if len(unknowns) == numRemainingMines:
                self.mines.update(unknowns)
                for unknown in unknowns:
                    print('New mine at ' + str(unknown[0]) +', ' + str(unknown[1]))
            # all the surrounding mine locations are known, so the unknown squares are safe
            elif number == len(mines):
                self.safeUnrevealed.update(unknowns)
                for unknown in unknowns:
                    print('New safe at ' + str(unknown[0]) +', ' + str(unknown[1]))
    
    def analyzeBoard(self):
        # remove any squares revealed by the last move from safeUnrevealed
        self.safeUnrevealed.difference_update({
            (i, j) for (i, j) in self.safeUnrevealed
                if super(MinesweeperSolver, self).safeGet((i,j)) != '?'
        })
        self.markSafeAndMines()

    def makeMove(self):
        if len(self.safeUnrevealed) > 0:
            safeMove = self.safeUnrevealed.pop()
            self.game.revealSquare(safeMove[0], safeMove[1])
            self.row, self.col = safeMove
        else:
            self.row, self.col = super(MinesweeperSolver, self).makeMove()

        return self.row, self.col
