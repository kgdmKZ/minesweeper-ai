# Author: Andrew Zadravec
#
# A simple Minesweeper terminal game which takes the row and column numbers
# of a square to reveal from STDIN and prints the board to STDOUT repeatedly
# until the game ends. When initialized with manual=True, there are no
# prompts (calls to revealSquare() can be used to change the state in order
# to reflect particular moves).
#

from random import randint
from minesweeper_messages import MinesweeperMessages as msg
import sys

class Minesweeper(object):
    defaultGameConfig = (16, 16, 40)

    def printBoard(self):
        charCols = 4*self.cols

        colNumberRow = '  ' + '   '.join(str(i+1) for i in
          range(min(9, self.cols))) + '   ' + '  '.join(str(j+1) for j
          in range(9, self.cols))

        print(colNumberRow)

        for i in range(self.rows):
            row = self.board[i]
            print("-" * charCols)
            print('| ' + ' | '.join(row) + ' |   ' + str(i+1))

        print("-" * charCols)

    def revealMinesInBoard(self):
        self.inProgress = False
        for i in range(self.rows):
            for j in range(self.cols):
                    if (i, j) in self.mineLocations:
                        self.board[i][j] = '*'
        self.printBoard()

    def rowAndColInBounds(self, row, col):
        rowInBounds = row >= 1 and row <= self.rows
        colInBounds = col >= 1 and col <= self.cols

        if not rowInBounds:
            print(msg.revealRowOutOfBounds)
        if not colInBounds:
            print(msg.revealColOutOfBounds)

        return rowInBounds and colInBounds

    def neverChosen(self, row, col):
        if self.safeGet((row-1, col-1)) != '?':
            print(msg.alreadyChosen)
            return False
        return True

    def validSquareRowCol(self, row, col):
        if self.rowAndColInBounds(row, col) and \
           self.neverChosen(row, col):
            return True
        return False

    def getValidSelection(self):
        while 1:
            rowCol = input(msg.revealMsg)
            rowCol = rowCol.split()

            if len(rowCol) != 2:
                print(msg.revealWrongFormat)
                continue

            try:
                row = int(rowCol[0])
                col = int(rowCol[1])
            except:
                print(msg.revealNotNumbers)
                continue

            if self.validSquareRowCol(row, col):
                return row-1, col-1

    def countMines(self, rowCol):
        row = rowCol[0]
        col = rowCol[1]

        adjacent = [(row-1,col-1),(row-1,col),(row-1,col+1),(row,col-1),
          (row, col+1),(row+1,col-1),(row+1,col),(row+1,col+1)]

        return sum(1 for square in adjacent if square in self.mineLocations)

    def safeGet(self, rowCol):
        row = rowCol[0]
        col = rowCol[1]

        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return None

        return self.board[row][col]

    def getAdjacentSquares(self, square):
        row = square[0]
        col = square[1]

        adjacent = [(row-1,col-1),(row-1,col),(row-1,col+1),
          (row,col-1), (row, col+1), (row+1,col-1),(row+1,col),(row+1,col+1)]

        return (rowCol for rowCol in adjacent if self.safeGet(rowCol) == '?')

    def getGameConfig(self):
        (rows, cols, mines) = (None, None, None)

        while 1:
            use_default = input(msg.gameStartMsg)

            if use_default.upper() == 'Y':
                return ()

            if use_default.upper() == 'N':
                while 1:
                    rows = input(msg.rowMsg)

                    try:
                        rows = int(rows)
                    except:
                        print(msg.rowNotNumber)
                        continue

                    if rows < 1:
                        print(msg.rowNone)
                    else:
                        break

                while 1:

                    cols = input(msg.colMsg)

                    try:
                        cols = int(cols)
                    except:
                        print(msg.colNotNumber)
                        continue

                    if cols < 1:
                        print(msg.colNone)
                    elif rows == 1 and cols == 1:
                        print(msg.colMakesBoardOneByOne)
                    else:
                        break

                while 1:

                    mines = input(msg.mineMsg)

                    try:
                        mines = int(mines)
                    except:
                        print(msg.mineNotNumber)

                    if mines < 1:
                        print(msg.mineNone)
                    elif mines >= rows*cols:
                        print(msg.mineTooMany)
                    else:
                        return rows, cols, mines

    @staticmethod
    def validGameConfig(game_config=()):
        return (len(game_config) == 3 and all(game_config) and
            game_config[2] < game_config[0]*game_config[1])

    def reset(self, game_config=()):
        self.inProgress = True
        self.seen = 0

        if self.validGameConfig(game_config):
            (self.rows, self.cols, self.mines) = game_config
        elif not (self.rows and self.cols and self.mines):
            (self.rows, self.cols, self.mines) = self.defaultGameConfig

        self.board = [['?'] * self.cols for i in range(self.rows)]

        self.mineLocations = set()

    def __init__(self, manual=False, game_config=()):
        (self.rows, self.cols) = (None, None)

        if manual:
            self.reset(game_config)
        else:
            game_config = self.getGameConfig()
            self.reset(game_config)
            self.printBoard()
            self.startGame()

    def placeMines(self, exclude=None):
        for i in range(self.mines):
            while 1:
                mineLocation = (
                    randint(0, self.rows-1),
                    randint(0, self.cols-1)
                )

                if (
                    exclude != mineLocation
                    and mineLocation not in self.mineLocations
                ):
                    self.mineLocations.add(mineLocation)
                    break

    def isWon(self):
        nonMineSquareCount = self.rows*self.cols-self.mines
        if self.seen == nonMineSquareCount:
            return True
        return False

    def revealSquare(self, row, col, printAfterReveal=True):
        print("\nRevealed square at (%d, %d)" % (row+1, col+1))

        square = self.board[row][col]

        if not self.mineLocations:
            # guarantee that the first selected square is not a mine
            self.placeMines(exclude=(row, col))
        elif (row, col) in self.mineLocations:
            self.revealMinesInBoard()
            print(msg.lost)
            return

        squares = set([(row,col)])

        while len(squares) > 0:
            for square in squares:
                self.seen += 1
                curCount = self.countMines(square)
                if curCount == 0:
                    self.board[square[0]][square[1]] = ' '
                else:
                    self.board[square[0]][square[1]] = str(curCount)

            newSquares = set()
            for square in squares:
                if self.safeGet(square) == ' ':
                    newSquares.update(self.getAdjacentSquares(square))

            squares = newSquares

        if self.isWon():
            self.revealMinesInBoard()
            print(msg.won)
        elif printAfterReveal:
            self.printBoard()

    def startGame(self):
        while self.inProgress:
            (row, col) = self.getValidSelection()
            self.revealSquare(row, col)

if __name__ == '__main__':
    Minesweeper()
