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
            rowCol = raw_input(msg.revealMsg)
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
        while 1:
            use_default = raw_input(msg.gameStartMsg)

            if use_default.upper() == 'Y':
                rows = 16
                cols = 16
                mines = 40
                return rows, cols, mines

            if use_default.upper() == 'N':
                while 1:
                    rows = raw_input(msg.rowMsg)

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
                    cols = raw_input(msg.colMsg)

                    try:
                        cols = int(cols)
                    except:
                        print(msg.colNotNumber)
                        continue

                    if cols < 1:
                        print(msg.colNone)
                    else:
                        break

                while 1:
                    mines = raw_input(msg.mineMsg)

                    try:
                        mines = int(mines)
                    except:
                        print(msg.mineNotNumber)

                    if mines < 1:
                        print(msg.mineNone)
                    elif mines >= self.rows*self.cols:
                        print(msg.mineTooMany)
                    else:
                        return rows, cols, mines


    def reset(self, rows, cols, mines):
        self.inProgress = True
        self.seen = 0

        self.rows = rows
        self.cols = cols
        self.mines = mines

        self.board = [['?'] * self.cols for i in range(self.rows)]

        self.placeMines()

    def __init__(self, manual=False, **config):
        if manual:
            rows = config.get('rows')
            cols = config.get('cols')
            mines = config.get('mines')
            self.reset(rows, cols, mines)
        else:
            rows, cols, mines = self.getGameConfig()
            self.reset(rows, cols, mines)
            self.printBoard()
            self.startGame()

    def placeMines(self):
        self.mineLocations = set()

        for i in range(self.mines):
            minePlaced = False

            while not minePlaced:
                mineRow = randint(0, self.rows-1)
                mineCol = randint(0, self.cols-1)

                if (mineRow, mineCol) not in self.mineLocations:
                    self.mineLocations.add((mineRow, mineCol))
                    minePlaced = True

    def isWon(self):
        nonMineSquareCount = self.rows*self.cols-self.mines
        if self.seen == nonMineSquareCount:
            return True
        return False

    def revealSquare(self, row, col):
        print("\nRevealed square at (%d, %d)" % (row+1, col+1))

        square = self.board[row][col]

        if (row, col) in self.mineLocations:
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
        else:
            self.printBoard()

    def startGame(self):
        while self.inProgress:
            (row, col) = self.getValidSelection()
            self.revealSquare(row, col)

if __name__ == '__main__':
    Minesweeper()
