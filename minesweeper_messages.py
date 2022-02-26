# Author: Andrew Zadravec
#
# This class contains messages displayed to Minesweeper players via STDOUT
# for various input prompts.
#

class MinesweeperMessages:
	# Message prompting player to choose a square to reveal
    revealMsg = "Enter a row and column number of the next square to reveal separated by a space:"

    # User entered something aside from 2 space-separated values
    revealWrongFormat = "Incorrect format: try again"

    # 2 provided values were not ints
    revealNotNumbers = "You must provide row and column numbers: try again"

    # Row number was out of bounds for the game board
    revealRowOutOfBounds = "Your row number is out of bounds: try again"

    # Col number was out of bounds for the game board
    revealColOutOfBounds = "Your column number is out of bounds: try again"

    # Message at the very start of a Minesweeper game
    gameStartMsg = "Use default game settings? (Answer Y/N)"

    # Prompts user to enter the number of rows a new game board should have
    rowMsg = "Enter the number of board rows: "

    # Value entered was not an int
    rowNotNumber = "You must enter a number of rows for the game board: try again"

    # Value would mean there are no rows, which is not allowed
    rowNone = "The game board must have at least one row: try again"

    # Prompts user to enter the number of game board columns
    colMsg = "Enter the number of board cols: "

    # Value was not an int
    colNotNumber = "You must enter a number of cols for the game board: try again"

    # Value was an int but would mean a zero-column game board
    colNone = "The game board must have at least one column: try again"

    # The user chose 1 for the number of rows on the game board and 1 for the number of columns.
    # This makes it impossible for at least one mine to be placed while leaving at least one safe
    # square, so prompt the user to give the game board at least 2 columns.
    colMakesBoardOneByOne = "The game board must be larger than one square. Choose a larger number of columns."
    
    # Prompt for user to enter the number of mines on a new game board
    mineMsg = "Enter the number of mines to place: "

    # Value was not an int
    mineNotNumber = "You must enter a number of mines for the game: try again"

    # Value meant there would be no mines on the board, which is not allowed
    mineNone = "The game board must have at least one mine: try again"

    # Value was too high, so every board square would have a mine
    mineTooMany = "The number of mines must allow for at least one safe square on the game board: try again"

    # Player won the game
    won = "YOU WIN: ALL SAFE SQUARES WERE REVEALED!"

    # Player lost the game
    lost = "GAME OVER: THAT SQUARE HAD A MINE!"

    # Player selected a square to reveal that has already been flipped
    alreadyChosen = "That square has already been revealed. Choose another."
