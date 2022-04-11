# minesweeper-ai

A terminal based Minesweeper game implementation, a simple framework for implementing an automated solver that plays games by submitting moves to an instance of the Minesweeper game, and one implementation of such an automated solver. The included solver has a win rate of
* ~92% for beginner difficulty games (9 rows, 9 columns, and 10 mines)
* ~80% for intermediate difficulty games (16 rows, 16 columns, and 40 mines)
* ~34% for expert difficulty games (30 rows, 16 columns, and 99 mines)

# Playing the game
Simply run `python minesweeper.py` and follow the prompts to configure the desired number of rows, columns, and mines in the game. You will then be prompted to input a row and column number separated by a space to indicate each desired move until the game ends. Between moves, the current state of the game board will be printed to the terminal.

# Creating an automated solver for the game
Create a subclass of `MinesweeperAI` that overrides `analyzeBoard()` and `determineMove()`. `determineMove()` must return a tuple where the first element is the desired row of the square to reveal and the second element is the desired column.

The base class `MinesweeperAI` includes methods to run the solver on particular game instances. It will conduct each turn by
1. Deciding on a square to reveal using `determineMove()`
2. Submitting the square as the next move to the game instance. The game board will update to reflect the move being made.
3. Running `analyzeBoard()` after the game board updates.

The last step above is the opportunity for your solver to update any internal state that may help in determining the next move.

By implementing the two methods indicated in your subclass, you will then be able to adapt the instructions below for running the existing solver implemented in the `MinesweeperSolver` class. Note that the `run` class method will need to be called on your new class to process the command line arguments, instantiate the class, and call `playGames()`.

# Running the automated solver
Run `python minesweeper_solver.py n r c m`
* This will complete `n` games using the solver.
* Each game will have `r` rows and `c` columns on the board, as well as `m` total mines on the board.
* `n`, `r`, `c`, and `m` must be positive integers.
* There must be at least one mine and one safe square on the game board.
* If the configuration indicated by the command line arguments is invalid, the solver will not proceed.

For each game, the solver will print out the initial game board and then the following for each move:
* the row and column of the square just revealed
* any mines and safe squares that were marked internally by the solver
* explanations for why mines and safes were marked
* the updated game board after the move
* an internal version of the updated game board that indicates the squares currently marked as mines and unrevealed safe squares.

For each completed game, the solver will print out the elapsed time and the total number of moves.

At the very end, the solver will print overall statistics for the completed games, namely number of wins, number of losses, win percentage, total time, and total moves across all the games.

# Solver algorithm description for each move
 1. Make a move by considering the following three options in order:
     * Select a square from the set of unrevealed squares known to be safe in any valid
        solution to the game (as derived from the current game board state). This is always
        the preferred option unless there are not any qualifying squares (this is the case in
        the very first turn, for example).
     * If the minimum of the estimated probabilities that each unknown square adjacent to any
        numbered square is a mine is less than the estimated probability that an arbitrary
        unknown square among those not adjacent to any numbered square contains a mine, then
        select the particular square with that minimum probability (or arbitrarily select one
        if there are multiple). This case does not apply when there are not yet any numbered
        squares.
     * Otherwise, select a square from the set of unknown squares not currently adjacent to
        any numbered square on the board. The preference is to select a random corner if any
        unrevealed corners remain that are not adjacent to a number, then edges if any squares
        are on one of the board's edges, and finally to select any random square not adjacent to
        a number if no corner or edge squares are unrevealed and non-adjacent to a number.

 2. Analyze the current board state for hints to replenish the set of unrevealed safe squares,
    increase the number of squares that are known to contain mines, estimate the relative
    probability that each unrevealed square next to at least one numbered square contains a mine,
    and determine the expected, minimum, and maximum mine total among all unrevealed squares next
    to at least one numbered square in valid partial solutions to the board for just those squares.

     * Check the squares surrounding each numbered square. If the number on the square combined
        with the solver's current record of squares that must be mines or must be safe means that
        the unrevealed squares with unknown status must all be mines (or must all be safe), then
        mark the squares accordingly. Do this repeatedly to catch cases where a newly marked
        square's status transitively impacts whether the unknown squares that share another
        adjacent numbered square must have certain statuses (and so on in a chain).
     * If the number of mines still unaccounted for that must be among the unknown squares
        surrounding the numbered square (as indicated by the gap between the square's number
        and the number of known adjacent mine squares) is the same as the number of mines
        still unaccounted for in the entire game, then all other unknown squares on the entire
        game board must be safe.
     * Determine the set of "frontiers" in the current game board:
         * A frontier is a set of unknown squares where knowing one square's status as either
            being safe or a mine potentially reveals the status that other unknown squares
            in the frontier must have because of constraints created by a chain of shared
            numbered squares and their adjacent unknown squares. The numbered squares adjacent
            to unknown squares in the frontier are also considered to be in the frontier.
         * All frontiers combined contain exactly the set of all squares on the game board
             that are unknown and have at least one adjacent numbered square, as well as all
             numbered squares adjacent to such squares.
         * A single frontier is constructed as follows:
                 * Start with an unknown square adjacent to at least one numbered square that
                    is not yet grouped into a frontier. Include it and its adjacent numbered
                    squares in the frontier being constructed.
                 * All unknown squares adjacent to the numbered squares just added are also
                    in the frontier, so add them.
                 * Add each numbered square adjacent to at least one of the unknown squares
                    added in step 2.
                 * Repeat steps 2 and 3 until either step yields no new squares to add.
     * For each frontier, enumerate all possible partial solutions to the board that satisfy
        the mine numbers on numbered squares in the frontier
         * "Partial solution" specifically means a unique marking of each unknown square in the
            frontier as either being a mine or safe that ensures all numbered squares have the
            correct numbers of adjacent mines. Future moves may determine that a given partial
            solution is actually not valid, but the point of creating partial solutions is to
            make an educated guess based on what can currently be derived from the board state.
         * Assign each unknown square an estimated probability that it is a mine by checking
             the number of partial solutions that set it as a mine divided by the number of
             partial solutions for its frontier.
         * Also record the "expected" total number of mines among all frontiers (the sum of
              average mine counts in partial solutions for each frontier), the minimum number
              of mines, and the maximum.
     * Use the minimum and maximum mine counts for the combined frontiers to reason about
        possible constraints on what the unknown squares outside the frontiers must be in
        order to satisfy the game's total mine count.
         * If the number of unknown (unmarked) mines left in the game matches the minimum
            number of mines among the frontiers' unknowns, all non-frontier unknowns must
            be safe, so mark them as such.
         * If the maximum number of mines among the frontiers would still leave a number
             of mines remaining in the game that matches the number of non-frontier unknowns,
             all non-frontier unknowns must be mines.
         * Note the expected number of mines among all unknowns in the frontiers is used in
              estimating the probability that picking a non-frontier unknown will yield a mine
              in the next move.



