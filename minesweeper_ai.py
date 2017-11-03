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
    
    # Resets instance variables to run a new Minesweeper game
    def nextGame(self, rows, cols, mines):
        self.game.reset(rows, cols, mines)

    # Examines the game board in the Minesweeper instance and updates the
    # data stored in this MinesweeperAI instance after a game move
    def analyzeBoard(self):
        # nothing to update
        pass
    
    # Determines the next game move and carries it out in the Minesweeper
    # instance
    def makeMove(self):
        while 1:
            row = randint(0, self.game.rows-1)
            col = randint(0, self.game.cols-1)    
            
            if self.game.board[row][col] == '?':
                self.game.revealSquare(row, col)

                break
    
    # Play one game with the specified numbers of rows, columns, and mines
    def playGame(self, rows, cols, mines):
        # reset the game with input configuration
        self.nextGame(rows, cols, mines)
        
        moves = 0
        start = time.time()
        
        while 1:
            self.makeMove()
            moves += 1
            if self.game.inProgress:
                self.analyzeBoard()
            else:
                break
        
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
    
    # Plays n games where game parameters are either random each time or fixed 
    # at the same rows, cols, mines values as given
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
    
    # Takes a tuple containing the row and column numbers of a square in the
    # game board and returns the string stored in the board, or None if the 
    # row and/or col numbers are out of bounds
    def safeGet(self, rowCol):
        rows = self.game.rows
        cols = self.game.cols

        row = rowCol[0]
        col = rowCol[1]

        if row < 0 or row >= rows or col < 0 or col >= cols:
            return None 
        
        return self.game.board[row][col]

    # A helper function to get a set of surrounding squares in the game board
    # given the row and column of a square. The set contains tuples where the 
    # first value is a tuple of row and column numbers and the second is the 
    # string stored in the board
    def getSurroundingSquares(self, row, col):
        adjacentRowCols = [(row-1,col-1),(row-1,col),(row-1,col+1),
          (row,col-1), (row, col+1), (row+1,col-1),(row+1,col),(row+1,col+1)]
        adjacentSquares = [(rowCol, self.safeGet(rowCol)) for rowCol in adjacentRowCols]
        return set([sq for sq in adjacentSquares if sq[1] is not None])

