# Author: Andrew Zadravec
#
# A simple Minesweeper Solver
#
# A high-level step-by-step description of the algorithm until the game ends:
#
# 1) Make a move by considering the following three options in order:
#
#     a) Select a square from the set of unrevealed squares known to be safe in any valid
#        solution to the game (as derived from the current game board state). This is always
#        the preferred option unless there are not any qualifying squares (this is the case in
#        the very first turn, for example).
#     b) If the minimum of the estimated probabilities that each unknown square adjacent to any
#        numbered square is a mine is less than the estimated probability that an arbitrary
#        unknown square among those not adjacent to any numbered square contains a mine, then
#        select the particular square with that minimum probability (or arbitrarily select one
#        if there are multiple). This case does not apply when there are not yet any numbered
#        squares.
#     c) Otherwise, select a square from the set of unknown squares not currently adjacent to
#        any numbered square on the board. The preference is to select a random corner if any
#        unrevealed corners remain that are not adjacent to a number, then edges if any squares
#        are on one of the board's edges, and finally to select any random square not adjacent to
#        a number if no corner or edge squares are unrevealed and non-adjacent to a number.
#
# 2) Analyze the current board state for hints to replenish the set of unrevealed safe squares,
#    increase the number of squares that are known to contain mines, estimate the relative
#    probability that each unrevealed square next to at least one numbered square contains a mine,
#    and determine the expected, minimum, and maximum mine total among all unrevealed squares next
#    to at least one numbered square in valid partial solutions to the board for just those squares.
#
#     a) Check the squares surrounding each numbered square. If the number on the square combined
#        with the solver's current record of squares that must be mines or must be safe means that
#        the unrevealed squares with unknown status must all be mines (or must all be safe), then
#        mark the squares accordingly. Do this repeatedly to catch cases where a newly marked
#        square's status transitively impacts whether the unknown squares that share another
#        adjacent numbered square must have certain statuses (and so on in a chain).
#     b) If the number of mines still unaccounted for that must be among the unknown squares
#        surrounding the numbered square (as indicated by the gap between the square's number
#        and the number of known adjacent mine squares) is the same as the number of mines
#        still unaccounted for in the entire game, then all other unknown squares on the entire
#        game board must be safe.
#     c) Determine the set of "frontiers" in the current game board:
#         i) A frontier is a set of unknown squares where knowing one square's status as either
#            being safe or a mine potentially reveals the status that other unknown squares
#            in the frontier must have because of constraints created by a chain of shared
#            numbered squares and their adjacent unknown squares. The numbered squares adjacent
#            to unknown squares in the frontier are also considered to be in the frontier.
#         ii) All frontiers combined contain exactly the set of all squares on the game board
#             that are unknown and have at least one adjacent numbered square, as well as all
#             numbered squares adjacent to such squares.
#         iii) A single frontier is constructed as follows:
#                 1) Start with an unknown square adjacent to at least one numbered square that
#                    is not yet grouped into a frontier. Include it and its adjacent numbered
#                    squares in the frontier being constructed.
#                 2) All unknown squares adjacent to the numbered squares just added are also
#                    in the frontier, so add them.
#                 3) Add each numbered square adjacent to at least one of the unknown squares
#                    added in step 2.
#                 4) Repeat steps 2 and 3 until either step yields no new squares to add.
#     d) For each frontier, enumerate all possible partial solutions to the board that satisfy
#        the mine numbers on numbered squares in the frontier
#         i) "Partial solution" specifically means a unique marking of each unknown square in the
#            frontier as either being a mine or safe that ensures all numbered squares have the
#            correct numbers of adjacent mines. Future moves may determine that a given partial
#            solution is actually not valid, but the point of creating partial solutions is to
#            make an educated guess based on what can currently be derived from the board state.
#         ii) Assign each unknown square an estimated probability that it is a mine by checking
#             the number of partial solutions that set it as a mine divided by the number of
#             partial solutions for its frontier.
#         iii) Also record the "expected" total number of mines among all frontiers (the sum of
#              average mine counts in partial solutions for each frontier), the minimum number
#              of mines, and the maximum.
#     e) Use the minimum and maximum mine counts for the combined frontiers to reason about
#        possible constraints on what the unknown squares outside the frontiers must be in
#        order to satisfy the game's total mine count.
#         i) If the number of unknown (unmarked) mines left in the game matches the minimum
#            number of mines among the frontiers' unknowns, all non-frontier unknowns must
#            be safe, so mark them as such.
#         ii) If the maximum number of mines among the frontiers would still leave a number
#             of mines remaining in the game that matches the number of non-frontier unknowns,
#             all non-frontier unknowns must be mines.
#         iii) Note the expected number of mines among all unknowns in the frontiers is used in
#              estimating the probability that picking a non-frontier unknown will yield a mine
#              in the next move.
#

from minesweeper_ai import MinesweeperAI
from minesweeper import Minesweeper
from random import randint
from math import ceil, log
from itertools import combinations
from multiprocessing import cpu_count, Pool

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

        # Estimated probabilities that each unknown square adjacent to at least
        # one revealed numbered square is a mine.
        self.squaresByProb = {}

        # expected number of mines among unrevealed squares adjacent to at least
        # one revealed numbered square, as well as the maximum and minimum
        self.expectedMineTotal = 0
        self.minMineTotal = 0
        self.maxMineTotal = 0

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
    def safeGet(self, row, col):
        if (row, col) in self.mines:
            return '*'

        if (row, col) in self.safeUnrevealed:
            return 'S'

        return super(MinesweeperSolver, self).safeGet(row, col)

    # Focus on just information that can be derived from one numbered square and its adjacent
    # squares to determine new squares that must be mines or safes.
    #
    # Parameters:
    #     (i, j): the row and column index of the numbered square on the board
    #     newMarks: a set of row and column indices for new mines/safes marked since the last turn
    #
    # Returns:
    #    whether the numbered square is complete, meaning there are no surrounding unknown squares
    #
    def analyzeNumSquare(self, i, j, newMarks):
        unknowns = self.getSurroundingSquares(i, j, self.isUnknown, self.justPosition)

        # This is not part of any of the board's current frontiers because it has no adjacent
        # squares with unknown values. When reasoning about where to make the next move, the
        # number indicated on this square is no longer useful, even if the final values
        # determined for adjacent squares are.
        if not unknowns:
            return True

        number = int(self.safeGet(i,j))
        mines = self.getSurroundingSquares(i, j, self.isMine, self.justPosition)

        numRemainingMines = number - len(mines)
        gameRemainingMines = self.game.mines - len(self.mines)
        numRemainingSafes = len(unknowns)-numRemainingMines
        allRemainingMinesAdj = numRemainingMines == gameRemainingMines

        # the game has the same number of mines left as this square must have among its unknowns
        if allRemainingMinesAdj:
            # every unrevealed, unmarked square not adjacent to this number square is guaranteed
            # to be safe
            nonAdjacentSafes = [
                (m, n)
                    for m in range(self.game.rows)
                    for n in range(self.game.cols)
                    if self.distance((i, j), (m, n)) > 1
                        and self.safeGet(m, n) == '?'
            ]

            if nonAdjacentSafes:
                self.safeUnrevealed.update(nonAdjacentSafes)
                newMarks.update(nonAdjacentSafes)

                print("Marked new safes:", *((m+1, n+1) for m, n in nonAdjacentSafes))
                print(
                    "    Reason: the number of unmarked mines left in the game matches the",
                    numRemainingMines, "unmarked mines that must be adjacent to the square",
                    "at", (i+1, j+1), "based on its mine number"
                )

        # the unknown squares are mines since their count matches the number of missing mines
        if not numRemainingSafes:
            self.mines.update(unknowns)
            newMarks.update(unknowns)

            print("Marked new mines:", *((m+1, n+1) for m, n in unknowns))
            print("    Reason: All unrevealed, unmarked squares adjacent to", (i+1, j+1),
                "need to be mines in order for the adjacent mine count to match the",
                "number on the square,", number)
        # the unknown squares are safe since there are no missing mines
        elif not numRemainingMines:
            self.safeUnrevealed.update(unknowns)
            newMarks.update(unknowns)

            print("Marked new safes:", *((m+1, n+1) for m, n in unknowns))
            print("    Reason: the total number of marked mines adjacent to square", (i+1, j+1),
                "is", number, "which matches the mine number on the square. The other",
                "adjacent squares must be safe")
        # this is still part of one of the frontiers in the current board state
        else:
            return False

        # just determined the values of all adjacent unknown squares
        return True

    # Returns the list of unknown squares that are not adjacent to at least one numbered square.
    # This is equivalent to the combination of all unknowns not in frontiers on the current board.
    def getNonFrontierUnknowns(self):
        return [
            (i, j)
                for i in range(self.game.rows)
                for j in range(self.game.cols)
                    if self.safeGet(i, j) == '?'
                        and not self.getSurroundingSquares(
                            i, j, self.isNum, transformGenFn=self.asCount
                        )
        ]

    # Considers the number of known mines and safes that have not been revealed, the revealed
    # numbered squares, and the minimum and maximum possible number of mines in a partial
    # solution to the board that fills in the status of only the unrevealed squares adjacent
    # to at least one revealed numbered square to determine whether the other unrevealed
    # squares must be all safe or all mines (taking advantage of the game's total mine count
    # being known as well).
    #
    # Returns whether any new mine or safe squares were marked.
    def checkFrontierMineRanges(self, frontiers):
        gameRemainingMines = self.game.mines - len(self.mines)
        nonFrontierUnknowns = self.getNonFrontierUnknowns()

        if not nonFrontierUnknowns:
            return False

        # Case 1: The maximum number of mines among the frontiers must be the actual number.
        #         There are just barely enough non-frontier unknowns to contain the rest of
        #         the game's remaining mines.
        if gameRemainingMines - self.maxMineTotal == len(nonFrontierUnknowns):
            self.mines.update(nonFrontierUnknowns)
            print("Marked new mines: ", *((i+1, j+1) for i, j in nonFrontierUnknowns))
            print("    Reason: there are just enough non-frontier unknown squares to contain",
                  "all remaining mines in the game if the frontiers contain the",
                  "maximum possible number of mines they can have.\n")
        # Case 2: The minimum number of mines among the frontiers must be the actual number.
        #         The game's remaining mines match this minimum, so all non-frontier unknowns
        #         cannot have mines.
        elif gameRemainingMines == self.minMineTotal:
            self.safeUnrevealed.update(nonFrontierUnknowns)
            print("Marked new safes: ", *((i+1, j+1) for i, j in nonFrontierUnknowns))
            print("    Reason: the minimum number of unmarked mines remaining in the frontiers",
                  "is the same as the total remaining unmarked mines in the game.",
                  "Therefore, all non-frontier unknown squares are safe.\n")
        else:
            return False

        return True

    # After the frontiers for the current turn have been derived, check that the total number of
    # mines left to find in the game board matches the total left in all frontiers, which
    # means any unknowns not adjacent to any numbered square (the non-frontier unknowns) must be
    # safe. Also check on a frontier by frontier basis in case all mines remaining are in just
    # one frontier.
    #
    # Returns whether any mines or safes were marked.
    def checkFrontiersWereSplitUp(self, frontiers):
        nums = [
            sum(
                int(self.safeGet(m, n))
                    - self.getSurroundingSquares(m, n, self.isMine, transformGenFn=self.asCount)
                for m, n in frontier[0]
            )
            for frontier in frontiers
        ]

        sumAllFrontiersNums = sum(nums)

        # Get the number of overlaps for each frontier. An overlap in this context means an unknown
        # square in the frontier that has more than one adjacent numbered square. If no overlaps
        # exist for a frontier, it has been split up by determining the status of each overlapping
        # square it originally contained. Only consider the provided unknown squares that are
        # actually still '?' on the internal board (not marked as mines or safes).
        overlaps = [
            sum(
                self.getSurroundingSquares(
                    m, n,
                    (lambda r, c, v: (r, c) in frontier[0]),
                    transformGenFn=self.asCount
                ) > 1
                for m, n in frontier[1]
                    if self.safeGet(m, n) == '?'
            )
            for frontier in frontiers
        ]

        sumAllFrontiersOverlaps = sum(overlaps)

        # There are still overlaps, so we can't just sum the numbers on the frontiers' numbered
        # squares to get the actual mine count within the frontiers in the solution.
        if sumAllFrontiersOverlaps:
            return False

        nonFrontierUnknowns = self.getNonFrontierUnknowns()

        # All unknowns are in the frontiers anyway, so we can't take advantage of the fact that the
        # game has a fixed, known total number of mines combined with the total mine count among
        # all the frontiers to deduce information about the mines/safes among the non-frontier
        # unknowns.
        if not nonFrontierUnknowns:
            return False


        origMineCount = len(self.mines)
        origSafeCount = len(self.safeUnrevealed)
        gameRemainingMines = self.game.mines - origMineCount

        # all mines are in the frontiers
        if sumAllFrontiersNums == gameRemainingMines:
            self.safeUnrevealed.update(nonFrontierUnknowns)

            print("Marked new safes: ", *((i+1, j+1) for i, j in nonFrontierUnknowns))
            print("\n")
            print("\n".join([
            "    Reasons:",
            "        1. the number of unmarked mines remaining in the whole game board is %d"
                     % (gameRemainingMines),
            "        2. no unknown square is adjacent to more than one numbered square",
            "        3. the sum of numbers on all numbered squares that have at least one",
            "           adjacent unknown square (subtracting the adjacent marked mines from",
            "           each number) is %d" % (gameRemainingMines),
            "        4. Since the numbers from reasons 1 and 3 match, each unknown square on",
            "           the game board that is not adjacent to any numbered square is safe"
            ]))
        # all non-frontier unknowns must be mines to match the total number of mines in the game
        elif len(nonFrontierUnknowns) == gameRemainingMines - sumAllFrontiersNums:
            self.mines.update(nonFrontierUnknowns)

            print("Marked new mines: ", *((i+1, j+1) for i, j in nonFrontierUnknowns))
            print("\n")
            print("\n".join([
            "    Reasons:",
            "        1. the number of unmarked mines remaining in the whole game board is %d"
                     % (gameRemainingMines),
            "        2. no unknown square is adjacent to more than one numbered square",
            "        3. the sum of numbers on all numbered squares that have at least one",
            "           adjacent unknown square (subtracting the adjacent marked mines from",
            "           each number) is %d" % (sumAllFrontiersNums),
            "        4. The number of unknown squares that are not adjacent to at least one",
            "           numbered square is %d" % (len(nonFrontierUnknowns)),
            "        5. The number from reason 4 is the same as the number from reason 1",
            "           with the number from reason 3 subtracted out"
            ]))
        else:
            return False

        return origMineCount != len(self.mines) or origSafeCount != len(self.safeUnrevealed)

    # Examine each numbered square's mine number in comparison to the number of adjacent squares
    # that are marked mines, marked safes, and unknowns to determine whether the unknowns can now
    # be marked.
    #
    # Returns whether any new mines or safes were marked.
    def analyzeNumSquaresInOrderFromNewMarks(self, frontiers, newMarks):
        origMarkCount = len(newMarks)

        for frontierNum in range(len(frontiers)):
            (numSquares, unknownSquares, newMarkSquares) = frontiers[frontierNum]

            for (m, n) in newMarkSquares:
                curDist = 0
                squares = []

                while len(squares) < len(numSquares):
                    squares.extend(
                        (p, q) for (p, q) in numSquares
                            if self.distance((p, q), (m, n)) == curDist
                    )
                    curDist += 1

                for (p, q) in squares:
                    self.analyzeNumSquare(p, q, newMarks)

                for (p, q) in reversed(squares):
                    self.analyzeNumSquare(p, q, newMarks)

            unknownSquares.difference_update([
                unknownSquare
                for unknownSquare in unknownSquares
                    if self.safeGet(*unknownSquare) != '?'
            ])

        return origMarkCount < len(newMarks)

    # Look at squares surrounding numbered squares to determine by elimination whether the unknown
    # squares must be mines or safe spaces that are guaranteed not to have mines. Consider the total
    # number of mines in the game and all possible valid partial solutions for each frontier to mark
    # additional mines and safes and to collect information about the possible numbers of mines
    # among the frontiers, the expected total number of mines among the frontiers, and the estimated
    # probability that each frontier unknown square is a mine given the current state of the board.
    def markSafeAndMines(self):
        seen = set()
        seenCondFn = self.seenFn(seen)
        notSeenCondFn = self.notCondFn(seenCondFn)

        newUnknown = self.composeCond(self.isUnknown, notSeenCondFn)
        newNum = self.composeCond(self.isNum, notSeenCondFn)

        frontierNums = set()
        inFrontier = self.seenFn(frontierNums)
        numInFrontier = self.composeCond(self.isNum, inFrontier)

        numberedSquares = [
            (i, j)
                for i in range(self.game.rows)
                for j in range(self.game.cols)
                if self.safeGet(i, j).isdigit()
        ]

        newMarks = set()

        # Look at each numbered square and its immediate surrounding squares in isolation first
        for (i, j) in numberedSquares:
            complete = self.analyzeNumSquare(i, j, newMarks)
            if complete:
                seen.add((i, j))

        # Look in a different order to get some cases where filling in unknowns around one numbered
        # square provides enough information to fill in the unknowns around a previous numbered square
        for (i, j) in reversed(numberedSquares):
            if (i, j) in seen:
                continue

            complete = self.analyzeNumSquare(i, j, newMarks)
            if complete:
                seen.add((i, j))

        # Build a list of frontiers to check independently from each other on the board. If a
        # numbered square is adjacent to either a second numbered square or an unknown square
        # adjacent to the second square, then the two numbered squares and their adjacent
        # unknowns are in the same frontier. If the second numbered square is adjacent to a third
        # numbered square or adjacent to an unknown square that is adjacent to the third numbered
        # square, all three squares are in the same frontier, and so on. Any configuration that
        # decides on each unknown square being a mine or not has no impact on another frontier,
        # but it will impact the possible configurations for this frontier.
        #
        # This is actually not entirely true because of the game having a fixed, known number of
        # mines. One frontier affects another only in the sense that one frontier may have
        # multiple possible configurations with different numbers of mines based on the information
        # currently derivable from the board state, and some of those configurations would not be
        # possible if other frontiers used more or fewer mines than a certain number.

        frontiers = []

        for (i, j) in numberedSquares:
            if (i, j) in seen:
                # Effectively, a numbered square without adjacent unknowns is no longer considered
                # to be in any frontier, so before this loop such squares were added to seen
                continue

            seen.add((i, j))

            # All adjacent unknowns are in the current frontier.
            unknowns = self.getSurroundingSquares(i, j, newUnknown, self.justPosition, self.asSet)
            seen.update(unknowns)

            # inFrontier and numInFrontier operate on this particular set, so for each iteration,
            # it needs to be cleared out so it can be used as a set for the current frontier. At
            # the end of the iteration, it gets copied so that in the final list of frontiers,
            # there will be a separate set of numbered squares for each frontier.
            frontierNums.clear()
            frontierNums.add((i, j))

            frontierUnknowns = set(unknowns)

            # Build the frontier by getting the new numbered squares adjacent to the current set of
            # unknown squares, then a set of new unknown squares adjacent to the new numbered
            # squares. This process ends when the set of new numbered squares is not adjacent to
            # any new unknown squares.
            while unknowns:
                nextNumbers=set()

                for m, n in unknowns:
                    nextNumbers.update(
                        self.getSurroundingSquares(m, n, newNum, self.justPosition, self.asIs)
                    )

                frontierNums.update(nextNumbers)
                seen.update(nextNumbers)
                unknowns.clear()

                for m, n in nextNumbers:
                    unknowns.update(
                        self.getSurroundingSquares(m, n, newUnknown, self.justPosition, self.asIs)
                    )

                frontierUnknowns.update(unknowns)
                seen.update(unknowns)

            # the newly marked squares that would be in this frontier had they not been marked
            frontierNewMarks = set(
                (m, n) for (m, n) in newMarks
                if self.getSurroundingSquares(
                    m, n, numInFrontier
                )
            )

            frontiers.append((frontierNums.copy(), frontierUnknowns, frontierNewMarks))

        markedSquares = True

        # Keep examining all the numbered squares and their adjacent unknowns to mark new squares
        # until there are no newly marked squares.
        while markedSquares and not self.safeUnrevealed:
            markedSquares = self.analyzeNumSquaresInOrderFromNewMarks(frontiers, newMarks)

        # Avoid enumerating all the possible solutions for each frontier to make a move decision
        # if a safe move is already known. Enumerating the solutions is expensive both in terms
        # of computational complexity and memory.
        if self.safeUnrevealed:
            return

        self.checkFrontiersWereSplitUp(frontiers)

        # Just as above, short circuit this method before determining all the partial solutions
        # for each frontier if at all possible.
        if self.safeUnrevealed:
            return

        newMarks.clear()

        for frontierNum in range(len(frontiers)):
            (numSquares, unknownSquares, newMarkSquares) = frontiers[frontierNum]

            unknownSquares = list(unknownSquares)

            # Use the index of each unknown square as the position in a bit vector of the bit
            # representing the unknown square being a mine in one of the partial solutions
            unknownSquarePositions = {
                unknownSquares[i] : i
                for i in range(len(unknownSquares))
            }

            # the number of unmarked mines remaining around each numbered square
            numSquareMinesRemaining = {
                (m, n) :
                int(self.safeGet(m, n)) -
                self.getSurroundingSquares(
                    m, n, self.isMine, transformGenFn=self.asCount
                )
                for (m, n) in numSquares
                    if int(self.safeGet(m, n)) -
                        self.getSurroundingSquares(
                            m, n, self.isMine, transformGenFn=self.asCount
                        )
            }

            # Build up solutions by starting with the partial solutions for each numbered square
            # in isolation. These partial solutions can then be merged into partial solutions for
            # the entire frontier in a later step.
            numSquareSolutions = {
                (m, n) : set()
                for (m, n) in numSquares
            }

            for (m, n) in numSquares:
                minesRemaining = numSquareMinesRemaining[(m,n)]
                numSquareUnknownPositions = [
                    unknownSquarePositions[(i, j)]
                    for (i, j) in self.getSurroundingSquares(
                        m, n, self.isUnknown, self.justPosition
                    )
                ]

                # A mask where the bits that are set are in the same positions as those
                # representing this numbered square's adjacent unknowns in the partial solution
                # bit vectors
                numSquareUnknownMask = sum(
                    1 << offset
                    for offset in numSquareUnknownPositions
                )

                # Iterate through each possible setting of bits just for the number of unkonwns
                # adjacent to this numbered square.
                for i in range(2**len(numSquareUnknownPositions)):
                    # To be a partial solution that satisfies this numbered square, the number of
                    # bits set must match the remaining mines required to be among this square's
                    # adjacent unknowns.
                    if i.bit_count() != minesRemaining:
                        continue

                    offset = 0
                    solution = 0
                    # Expand i into the equivalent solution where the bit for each unknown is in
                    # the right place (so including zeroes for all the positions representing
                    # unknowns in this frontier that are not adjacent to this numbered square).
                    solution = sum(
                        1 << numSquareUnknownPositions[offset]
                        for offset in range(len(numSquareUnknownPositions))
                        if (i >> offset) & 1
                    )

                    # Partial solutions are actually represented using two separate bit vectors.
                    #
                    # The first one has a bit set in the appropriate position for each unknown
                    # square in the frontier that has been set as a mine so far (so only ones
                    # adjacent to this numbered square for now).
                    #
                    # The second has a bit set instead in the appropriate position for each
                    # unknown that must not be a mine in this partial solution (meaning that any
                    # valid solution built on top of this one must not set mines in those
                    # positions or the number of mines would exceed this square's mine number)
                    #
                    # Example:
                    #
                    # If this numbered square is the only one in the frontier, and there are
                    # three unknowns but only two mines, a possible solution bit vector that
                    # sets two of the mines is 110. The second bit vector in the solution would
                    # then be 001 because for the partial solution to remain valid with further
                    # mine settings, no more unknowns adjacent to this square could be set to
                    # mines.
                    numSquareSolutions[(m, n)].add(
                        (solution, solution ^ numSquareUnknownMask)
                    )

            # Pick an arbitrary reference square and order the numbered squares by their distance
            # from it in order to keep numbered squares that share adjacent unknowns with each other
            # closer together in the ordering.
            #
            # This is important so that when partial solutions are merged, the total number of
            # partial solutions afterward is kept as low as possible. It is better for memory usage
            # and total runtime if the partial solutions set mines and forbid mines in as many
            # overlapping positions as possible so that they are more likely to either match each
            # other (duplicate solutions only need to be included once, not twice) or not be
            # combinable because one solution sets a mine in a position forbidden by the other one.
            numSquaresByDistFromRefSquare = list(numSquares)
            referenceSq = numSquaresByDistFromRefSquare[0]
            numSquaresByDistFromRefSquare.sort(
                key=(lambda sq: self.distance(referenceSq, sq))
            )

            partialSolutionSets = [
                numSquareSolutions[sq]
                for sq in numSquaresByDistFromRefSquare
            ]

            # This is the merge step. Starting with isolated partial solutions that just solve
            # each numbered square in the frontier independently, progressively build up the
            # set of partial solutions that satisfy all mine numbers on squares in the frontier
            # at once. This is done by doubling the number of solved numbered squares in each
            # partial solution in each iteration.
            while len(partialSolutionSets) > 1:
                for i in range(len(partialSolutionSets) // 2):
                    numSquare1Sols = partialSolutionSets[2*i]
                    numSquare2Sols = partialSolutionSets[2*i+1]

                    # A partial solution that represents the combination of two other partial
                    # solutions will set a mine on each square where a mine was set in at least
                    # one of the other partial solutions. Doing a bitwise or accomplishes this
                    # for the bit vector representation of mine settings.
                    #
                    # Doing a bitwise or on the second bit vectors of each (the one that indicates
                    # squares that must not have a mine) yields the combined set of squares that
                    # must not have mines in the new partial solution.
                    #
                    # If a 1 is set at the same position in both the first and second bit vectors
                    # of the new combined partial solution, that means there is a conflict: one
                    # of the old partial solutions must have forbidden setting a mine in a position
                    # where the other solution set one. Therefore, the combined partial solution
                    # is invalid and should not go on to the next iteration of this merge step.
                    partialSolutionSets[2*i] = {
                        (solMines1 | solMines2, solNotMines1 | solNotMines2)
                        for (solMines1, solNotMines1) in numSquare1Sols
                        for (solMines2, solNotMines2) in numSquare2Sols
                            if (solNotMines1 | solNotMines2) & (solMines1 | solMines2) == 0
                    }
                    numSquare2Sols.clear()

                # Now there should be around half as many partial solution sets since sets
                # were merged in the for loop above. Empty sets represent that a solution set
                # was merged into a different solution set at some other index, so empty sets
                # should be removed.
                partialSolutionSets = [
                    partialSolutionSet
                    for partialSolutionSet in partialSolutionSets
                        if partialSolutionSet
                ]

            # Remove extraneous solutions that choose to set too many mines in this frontier,
            # causing the total number of mines in the game to be too high.
            sols = [
                sol
                for (sol, _) in partialSolutionSets[0]
                    if sol.bit_count() <= self.game.mines-len(self.mines)
            ]

            minesSetEachSol = [sol.bit_count() for sol in sols]
            mineBitsSet = sum(minesSetEachSol)
            numSolutions = len(sols)

            # Map the row and column index of each unknown square in this frontier to the number
            # of solutions for the frontier that mark the unknown square as a mine.
            solutionsWhereMine = {
                (i, j) : sum(
                    1 for sol in sols
                    if sol & (1 << unknownSquarePositions[(i, j)])
                )
                for (i, j) in unknownSquares
            }

            # Add the average number of mine bits set in a solution to the total expected for all
            # the frontiers combined.
            self.expectedMineTotal += mineBitsSet / numSolutions

            self.minMineTotal += min(minesSetEachSol)
            self.maxMineTotal += max(minesSetEachSol)

            for unknown in unknownSquares:
                mineSolutionsCount = solutionsWhereMine[unknown]
                printUnknown = (unknown[0]+1, unknown[1]+1)

                if mineSolutionsCount == 0:
                    print("Marked new safe:", printUnknown)
                    print("    Reason: no solutions have a mine at this square\n")

                    # no potential solution sets this unknown as a mine, so it must be safe
                    self.safeUnrevealed.add(unknown)

                    # knowing at least one safe, unrevealed square is good enough to determine
                    # the next move
                    return

                if mineSolutionsCount == numSolutions:
                    print("Marked new mine:", printUnknown),
                    print("    Reason: all potential solutions have a mine at this square\n")

                    # every potential solution sets this unknown as a mine, so it must be a mine
                    self.mines.add(unknown)
                    newMarks.add(unknown)

                    self.minMineTotal -= 1
                    self.maxMineTotal -= 1
                    self.expectedMineTotal -= 1
                else:
                    # Estimate the probability that the game really has a mine at this square.
                    # This is an estimate not only because some solutions may be more likely than
                    # others, but also because the total mine count in the game combined with one
                    # frontier's mine count may determine what another frontier's total mine count
                    # is constrained to be (in cases where partial solutions allow more than one
                    # possible mine count for the frontier).
                    prob = mineSolutionsCount/numSolutions

                    if prob in self.squaresByProb:
                        self.squaresByProb[prob].append(unknown)
                    else:
                        self.squaresByProb[prob] = [unknown]

        oldMines = self.mines.copy()

        markedSquares = True

        # Examine all the numbered squares and their adjacent unknowns for new safes/mines to mark,
        # stopping when one round yields no new marked squares or a safe, unrevealed square was
        # marked (so the next move can be that square).
        while markedSquares and not self.safeUnrevealed:
            markedSquares = self.analyzeNumSquaresInOrderFromNewMarks(frontiers, newMarks)

        # The mine totals from the frontier partial solutions step may need to be updated if more
        # mines were just added. Known mines are no longer considered to be in any frontier.
        minesAdded = len(self.mines.difference(oldMines))
        self.maxMineTotal = max(0, self.maxMineTotal-minesAdded)
        self.minMineTotal = max(0, self.minMineTotal-minesAdded)
        self.expectedMineTotal = max(0, self.expectedMineTotal-minesAdded)

        # The maximum mine total among the frontier unknowns cannot possibly exceed the number of
        # mines left in the game, and the minimum needs to be at least whatever number of mines
        # would be left in the game if all the non-frontier unknowns were assumed to be mines.
        self.maxMineTotal = min(self.maxMineTotal, self.game.mines - len(self.mines))
        self.minMineTotal = max(
            self.minMineTotal,
            self.game.mines - len(self.mines) - len(self.getNonFrontierUnknowns())
        )
        self.expectedMineTotal = max(self.minMineTotal, self.expectedMineTotal)
        self.expectedMineTotal = min(self.maxMineTotal, self.expectedMineTotal)

        # Use the total mine count range for the combined frontiers to decide if the current state
        # of the game board indicates the non-frontier unknowns must be mines or safes.
        self.checkFrontierMineRanges(frontiers)
        self.checkFrontiersWereSplitUp(frontiers)

        # It is possible some mines were just marked, and squaresByProb should only have squares
        # that are candidates for the next move, so remove any mines.
        self.squaresByProb = {
            prob : [
                sq for sq in self.squaresByProb[prob]
                    if sq not in self.mines
            ]
            for prob in self.squaresByProb
                if any(
                    sq for sq in self.squaresByProb[prob]
                        if sq not in self.mines
                )
        }

    # After a move, examine the board to gain insight into what the best options are for the next
    # move. This includes updating the state of this MinesweeperSolver instance to reflect mine
    # probabilities for certain squares, mark new safes, and mark new mines.
    def analyzeBoard(self):
        # remove any squares revealed by the last move from safeUnrevealed
        self.safeUnrevealed.difference_update({
            (i, j) for (i, j) in self.safeUnrevealed
                if super(MinesweeperSolver, self).safeGet(i,j) != '?'
        })

        self.squaresByProb = {}
        self.expectedMineTotal = 0
        self.minMineTotal = 0
        self.maxMineTotal = 0

        self.markSafeAndMines()

    # Select a move from a list of candidate moves. Randomly select a corner if there is one.
    # Otherwise, randomly select a square on the edge of the board if there is one. If the
    # potential moves include neither a corner square nor an edge square, randomly select
    # any of the squares.
    def selectMovePreferCornersEdges(self, potentialMoves):
        moveCorner = [
            (i, j) for (i, j) in potentialMoves
            if (i == 0 or i == self.game.rows-1) and (j == 0 or j == self.game.cols-1)
        ]
        if moveCorner:
            moveIndex = randint(0, len(moveCorner)-1)
            return moveCorner[moveIndex]

        moveEdge = [
            (i, j) for (i, j) in potentialMoves
            if i == 0 or i == self.game.rows-1 or j == 0 or j == self.game.cols-1
        ]
        if moveEdge:
            moveIndex = randint(0, len(moveEdge)-1)
            return moveEdge[moveIndex]

        moveIndex = randint(0, len(potentialMoves)-1)
        return potentialMoves[moveIndex]

    # Make the next move. Always pick a known safe, unrevealed square if there is one.
    # Otherwise, decide between selecting a frontier square known to be the least likely
    # frontier square to have a mine or selecting a random non-frontier square based on whether that
    # is estimated to have a lower probability of being a mine.
    def determineMove(self):
        if self.safeUnrevealed:
            move = self.safeUnrevealed.pop()
            print("Move strategy: select an unrevealed square that is known to be safe")
        else:
            minesNotInFrontiers = self.game.mines - len(self.mines) - self.expectedMineTotal
            nonFrontierUnknowns = self.getNonFrontierUnknowns()

            # Estimated mine probabilities for frontier squares are available and there are eitehr
            # no unknowns outside the frontiers or the minimum probability frontier square has a
            # lower probability of being a mine than a random non-frontier square.
            if (
                self.squaresByProb and (
                    not nonFrontierUnknowns or
                    min(self.squaresByProb) <=
                        minesNotInFrontiers/len(nonFrontierUnknowns)
                )
            ):
                print("Move strategy: select the unrevealed frontier square least likely to have",
                      "a mine")
                minProb = min(self.squaresByProb)
                minProbSquares = self.squaresByProb[minProb]
                move = self.selectMovePreferCornersEdges(minProbSquares)
            elif nonFrontierUnknowns:
                print(
                    "Move strategy: select a random unrevealed square outside the current",
                    "frontiers"
                )
                move = self.selectMovePreferCornersEdges(nonFrontierUnknowns)
            else:
                print("Move strategy: select a random unrevealed square")
                unknownsOnBoard = [
                    (i, j)
                        for i in range(self.game.rows)
                        for j in range(self.game.cols)
                            if self.game.safeGet((i, j)) == '?'
                ]
                moveIndex = randint(0, len(unknownsOnBoard)-1)
                move = unknownsOnBoard[moveIndex]

        (self.row, self.col) = move
        return move

    # Print both the game board and a special internal version of the board that includes extra
    # information (namely the solver's marked mine and unrevealed safe square locations).
    def printBoard(self):
        print("\nGame Board:")
        self.game.printBoard()
        print("Internal Board:")
        boardWidth = 4*self.game.cols
        colNumberRow = '  ' + '   '.join(str(i+1) for i in
          range(min(9, self.game.cols))) + '   ' + '  '.join(str(j+1) for j
          in range(9, self.game.cols))

        print(colNumberRow)

        for i in range(self.game.rows):
            row = [ self.safeGet(i, j) for j in range(self.game.cols) ]
            print("-" * boardWidth)
            print('| ' + ' | '.join(row) + ' |   ' + str(i+1))

        print("-" * boardWidth, "\n")

if __name__ == '__main__':
    MinesweeperSolver.run()
