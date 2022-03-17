# Author: Andrew Zadravec
#
# A simple Minesweeper Solver
from minesweeper_ai import MinesweeperAI
from random import randint
from math import ceil
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
        # The minimum estimated probability that an unknown square adjacent to
        # at least one revealed numbered square is a mine.
        self.minProb = 1
        # The square corresponding to minProb
        self.minProbSquare = None
        # expected number of mines among unrevealed squares adjacent to at least
        # one revealed numbered square
        self.expectedMineTotal = 0
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
                        and self.safeGet(i, j) == '?'
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
            print("Marked new safes: ", *((m+1, n+1) for m, n in unknowns))
            print("    Reason: the total number of marked mines adjacent to square", (i+1, j+1),
                "is", number, "which matches the mine number on the square. The other",
                "adjacent squares must be safe")
        # this is still part of one of the frontiers in the current board state
        else:
            return False
        # just determined the values of all adjacent unknown squares
        return True

    def mapOverSolutions(
        self, exclusiveMaxSol, numSquareMaskMines,
        mapFunc, resFunc, chunkSize=1000
    ):
        with Pool(cpu_count()) as p:
            res = resFunc(
                p.unordered_imap(
                    mapFunc,
                    self.solutionsChunkGenerator(0, exclusiveMaxSol, numSquareMaskMines),
                    chunkSize
                )
            )
        return res

    def solutionsChunkGenerator(self, minSol, exclusiveMaxSol, numSquareMaskMines):
        maxMines = sum(numSquareMaskMines.values())
        for i in range(minSol, exclusiveMaxSol):
            if i.bit_count() > maxMines:
                continue
            allMineNumbersMatchSol = True
            for mask in numSquareMaskMines:
                if (mask & i).bit_count() != numSquareMaskMines[mask]:
                    allMineNumbersMatchSol = False
                    break
            if allMineNumbersMatchSol:
                yield i

    def solutionInfo(
        self, exclusiveMaxSol, numSquareMaskMines, unknownSquares, chunkSize=1000000
    ):
        numSolutions = 0
        mineBitsSet = 0
        solutionsWhereMine = {
            unknown : 0
            for unknown in unknownSquares
        }
        print("chunkSize is", chunkSize, "because nSMM and uS are", len(numSquareMaskMines), len(unknownSquares))
        chunks = ceil(exclusiveMaxSol/chunkSize)
        for chunk in range(chunks):
            firstInChunk = chunk*chunkSize
            chunkBound = min(firstInChunk+chunkSize, exclusiveMaxSol)
            for sol in self.solutionsChunkGenerator(
                firstInChunk, chunkBound, numSquareMaskMines
            ):
                numSolutions += 1
                mineBitsSet += sol.bit_count()

                offset = 0

                while sol >> offset:
                    if (sol >> offset) & 1:
                        solutionsWhereMine[unknownSquares[offset]] += 1
                    offset += 1
        return (numSolutions, mineBitsSet, solutionsWhereMine)

    # Look at squares surrounding numbered squares to determine
    # by elimination whether the unknown squares must be mines
    # or safe spaces that are guaranteed not to have mines
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
        for (i, j) in reversed(numberedSquares):
            if (i, j) in seen:
                continue
            complete = self.analyzeNumSquare(i, j, newMarks)
            if complete:
                seen.add((i, j))

        frontiers = []
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
        for (i, j) in numberedSquares:
            if (i, j) in seen:
                continue

            seen.add((i, j))
            unknowns = self.getSurroundingSquares(i, j, newUnknown, self.justPosition, self.asSet)
            seen.update(unknowns)
            frontierNums.clear()
            frontierNums.add((i, j))
            frontierUnknowns = set(unknowns)
 
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

            frontierNewMarks = set(
                (m, n) for (m, n) in newMarks
                if self.getSurroundingSquares(
                    m, n, numInFrontier
                )
            )

            frontiers.append((frontierNums.copy(), frontierUnknowns, frontierNewMarks))

        # Now that the frontiers for this turn have been derived, check that the total
        # mines left to find in the game board matches the total left in all frontiers, which
        # means any unknowns not adjacent to any numbered square (meaning it is not in any of
        # the frontiers) must be safe. Also check on a frontier by frontier basis in case all
        # mines remaining are in just one frontier.
        nums = [
            sum(
                int(self.safeGet(m, n))
                    - self.getSurroundingSquares(m, n, self.isMine, transformGenFn=self.asCount)
                for m, n in frontier[0]
            )
            for frontier in frontiers
        ]

        sumAllFrontiersNums = sum(nums)

        overlaps = [
            sum(
                self.getSurroundingSquares(
                    m, n,
                    (lambda r, c, v: (r, c) in frontier[0]),
                    transformGenFn=self.asCount
                ) > 1
                for m, n in frontier[1]
            )
            for frontier in frontiers
        ]

        sumAllFrontiersOverlaps = sum(overlaps)
        gameRemainingMines = self.game.mines - len(self.mines)
        allRemainingMinesInOneFrontier = False

        for frontierIdx in range(len(nums)):
            if (nums[frontierIdx] != gameRemainingMines or overlaps[frontierIdx]):
                continue

            allRemainingMinesInOneFrontier = True
            outsideThisFrontierUnknowns = [
                (i, j)
                    for i in range(self.game.rows)
                    for j in range(self.game.cols)
                        if self.safeGet(i, j) == '?'
                            and not self.getSurroundingSquares(
                                i, j,
                                (lambda r, c, v: (r, c) in frontiers[frontierIdx][0]),
                                transformGenFn=self.asCount
                            )
            ]

            if outsideThisFrontierUnknowns:
                self.safeUnrevealed.update(outsideThisFrontierUnknowns)
                print("All mines must be in the frontier formed by the following squares: \n   ",
                *((i+1, j+1) for i, j in frontiers[frontierIdx][0]), "(Numbered squares)\n   ",
                *((i+1, j+1) for i, j in frontiers[frontierIdx][1]), "(Unknown squares)",
                "\nA frontier means all numbered squares have at least one unrevealed, unmarked",
                "\nadjacent square, all such adjacent squares are also in the frontier, and any",
                "\nnumbered squares that share an adjacent unknown square with any number in the",
                "\nfrontier is also considered to be part of the same frontier\n\n"
                )
                print("Marked new safes: ", *((i+1, j+1) for i, j in outsideThisFrontierUnknowns))
                print("\n")
                print("\n".join([
                "    Reasons:",
                "        1. the number of unmarked mines remaining in the whole game board is %d"
                         % (gameRemainingMines),
                "        2. no unknown square in the frontier defined above is adjacent to more ",
                "           than one numbered square in the frontier",
                "        3. the sum of numbers on all numbered squares in the frontier",
                "           (subtracting the adjacent marked mines from each number) is %d"
                            % (gameRemainingMines),
                "        4. Since the numbers from reasons 1 and 3 match, each unknown square on",
                "           the game board that is not adjacent to any numbered square in the ",
                "           frontier is safe"
                ]))

        # maybe all the remaining mines in the game are known to be in the frontiers, so it should
        # be the case that every unknown square on the board outside of the ones within the current
        # frontiers is safe
        if (
            sumAllFrontiersNums == gameRemainingMines and not sumAllFrontiersOverlaps
            and not allRemainingMinesInOneFrontier
        ):
            nonFrontierUnknowns = [
                (i, j)
                    for i in range(self.game.rows)
                    for j in range(self.game.cols)
                        if self.safeGet(i, j) == '?'
                            and not self.getSurroundingSquares(
                                i, j, self.isNum, transformGenFn=self.asCount
                            )
            ]

            if nonFrontierUnknowns:
                self.safeUnrevealed.update(nonFrontierUnknowns)
                print("Marked new safes: ", *((i+1, j+1) for i, j in nonFrontierUnknowns))
                print("\n")
                print("\n".join([
                "    Reasons:",
                "        1. the number of unmarked mines remaining in the whole game board is %d"
                         % (gameRemainingMines),
                "        2. no unknown square is adjacent to more than one numbered square",
                "        3. the sum of numbers on all numbered squares that have at least one",
                "           adjacent unknown square (subtracting the adjacent marked mines from ",
                "           each number) is %d" % (gameRemainingMines),
                "        4. Since the numbers from reasons 1 and 3 match, each unknown square on",
                "           the game board that is not adjacent to any numbered square is safe"
                ]))

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

            for repeat in range(max(self.game.rows, self.game.cols)):
                for (p, q) in numSquares:
                    self.analyzeNumSquare(p, q, newMarks)

            unknownSquares.difference_update([
                unknownSquare
                for unknownSquare in unknownSquares
                    if self.safeGet(*unknownSquare) != '?'
            ])

        if self.safeUnrevealed:
            return

        for frontierNum in range(len(frontiers)):
            (numSquares, unknownSquares, newMarkSquares) = frontiers[frontierNum]

            unknownSquares = list(unknownSquares)

            solutionExclusiveMaxBound = (1 << len(unknownSquares))
            unknownSquarePositions = {
                unknownSquares[i] : i
                for i in range(len(unknownSquares)) 
            }

            numSquareMaskMines = {
                sum(
                    1 << unknownSquarePositions[(i, j)]
                        for i in range(m-1, m+2)
                        for j in range(n-1, n+2)
                            if (i, j) in unknownSquarePositions
                ) :
                int(self.safeGet(m, n)) -
                sum(
                    1
                        for i in range(m-1, m+2)
                        for j in range(n-1, n+2)
                            if (i, j) in self.mines
                )
                for (m, n) in numSquares
                if int(self.safeGet(m, n)) - sum(
                    1
                        for i in range(m-1, m+2)
                        for j in range(n-1, n+2)
                            if (i, j) in self.mines
                )
            }

            (numSolutions, mineBitsSet, solutionsWhereMine) = self.solutionInfo(
                solutionExclusiveMaxBound, numSquareMaskMines, unknownSquares
            )

            self.expectedMineTotal += mineBitsSet / numSolutions
            for unknown in unknownSquares:
                mineSolutionsCount = solutionsWhereMine[unknown]
                print("solutions where mine is", solutionsWhereMine)
                if mineSolutionsCount == numSolutions:
                    # every potential solution sets this unknown as a mine, so it must be a mine
                    print("all solutions have a mine here")
                    self.mines.add(unknown)
                elif mineSolutionsCount == 0:
                    print("no solutions have a mine here")
                    # no potential solution sets this unknown as a mine, so it must be safe
                    self.safeUnrevealed.add(unknown)
                    return
                elif (prob := mineSolutionsCount/numSolutions) <= self.minProb:
                    # note the proportion of potential solutions where this square is a mine
                    print("setting minProb to prob", prob)
                    self.minProb = prob
                    self.minProbSquare = unknown

    def analyzeBoard(self):
        # remove any squares revealed by the last move from safeUnrevealed
        self.safeUnrevealed.difference_update({
            (i, j) for (i, j) in self.safeUnrevealed
                if super(MinesweeperSolver, self).safeGet(i,j) != '?'
        })
        self.minProb = 1
        self.minProbSquare = None
        self.expectedMineTotal = 0

        self.markSafeAndMines()

    def makeMove(self):
        if self.safeUnrevealed:
            move = self.safeUnrevealed.pop()
            print("Move strategy: select an unrevealed square that is known to be safe")
        else:
            minesNotInFrontiers = self.game.mines - len(self.mines) - self.expectedMineTotal
            unknownsNotInFrontiers = [
                (i, j)
                    for i in range(self.game.rows)
                    for j in range(self.game.cols)
                        if self.safeGet(i, j) == '?' 
                            and not self.getSurroundingSquares(i, j, self.isNum)
            ]

            if (
                unknownsNotInFrontiers
                and self.minProb > minesNotInFrontiers/len(unknownsNotInFrontiers)
            ):
                print("Move strategy: select an unrevealed square outside the current frontiers")
                moveIndex = randint(0, len(unknownsNotInFrontiers)-1)
                move = unknownsNotInFrontiers[moveIndex]
            elif self.minProbSquare:
                print("Move strategy: select the unrevealed frontier square least likely to have",
                      "a mine")
                print("minProbSquare is", self.minProbSquare)
                move = self.minProbSquare
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

        self.game.revealSquare(*move, False)
        (self.row, self.col) = move

    def printBoard(self):
        print("Game Board:")
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
