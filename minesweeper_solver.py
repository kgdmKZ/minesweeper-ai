from minesweeper_ai import MinesweeperAI
from random import randint

class MinesweeperSolver(MinesweeperAI):
    def __init__(self):
        super(MinesweeperSolver, self).__init__()
        
        # contain (row, col) for each known mine and each known safe '?' square
        self.mines = set()
        self.safeUnrevealed = set() 

        # row and column of most recent game move
        self.row = None
        self.col = None
    
    # use MinesweeperAI safeGet() method but change some values from the board
    # in cases where mines or safeUnrevealed contain them
    def safeGet(self, rowCol):
        if rowCol in self.mines:
            return '*'
        if rowCol in self.safeUnrevealed:
            return 'S'

        return super(MinesweeperSolver, self).safeGet(rowCol)

    # Identifies mines in the game board that are next to newly-revealed '1'
    # squares in cases where all other squares surrounding those ones are 
    # revealed
    def markByOnes(self):
        squareVal = self.safeGet((self.row, self.col))
        squaresRevealed = set([((self.row, self.col), squareVal)])
        seen = set()

        while len(squaresRevealed) > 0:
            curSquare = squaresRevealed.pop()
            row, col = curSquare[0][0], curSquare[0][1]
            squareVal = curSquare[1]

            surrounding = self.getSurroundingSquares(row, col)
            
            if squareVal == '1':
                unknowns = [sq for sq in surrounding if sq[1] == '?']
                if len(unknowns) == 1:
                    rowColMine = unknowns[0][0]
                    self.mines.add(rowColMine)
            elif squareVal == ' ':
                surrounding = [sq for sq in surrounding if \
                  sq[1] in (' ', '1') and sq[0] not in seen]
                squaresRevealed.update(surrounding)

            seen.add(curSquare[0])
    
    def analyzeBoard(self):
        self.markByOnes()

    def makeMove(self):
        if len(self.safeUnrevealed) > 0:
            safeMove = self.safeUnrevealed.pop()
            self.game.revealSquare(safeMove[0], safeMove[1])
            self.row, self.col = safeMove
        else:
            while 1:
                row = randint(0, self.game.rows-1)
                col = randint(0, self.game.cols-1)    
                
                if self.game.board[row][col] == '?' and \
                  (row, col) not in self.mines:
                    self.game.revealSquare(row, col)
                    self.row, self.col = row, col
                    break    


            