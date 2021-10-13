from copy import deepcopy
import json
import time

class LittleGo:

    def parseInput(self, filename = 'input.txt'):
        'Function to read the input and store data'

        with open(filename) as f:
            l = f.readlines()

        self.player = int(l[0].strip())
        self.past = [[int(j) for j in i[:5]] for i in l[1:6]]
        self.current = [[int(j) for j in i[:5]] for i in l[6:11]]
        self.skip = True
        self.komi = 2.5 if self.player == 2 else -2.5
        self.score = self.evaluate(self.current)
        
        #to find number of moves played
        flag = True
        count = 0
        for i in self.current:
            for j in i:
                if j!=0:
                    flag = False
                    count += 1
                    if count > 1:
                        break

        if flag:
            self.moves = 0
        elif count == 1:
            self.moves = 1
        else:
            data = json.load(open('misc.json'))
            self.moves = data['moves']

    def getNeighbours(self, i, j):
        'Function to return all neighbours of a coin'

        neighbours = []

        if i>0: neighbours += [(i-1, j)]
        if i<4: neighbours += [(i+1, j)]
        if j>0: neighbours += [(i, j-1)]
        if j<4: neighbours += [(i, j+1)]

        return neighbours

    def countLiberties(self, board, player):
        'Function to count total number of liberties for a player'

        liberties = 0

        for i in range(5):
            for j in range(5):
                if board[i][j]==0:
                    for n in self.getNeighbours(i, j):
                        if board[n[0]][n[1]] == player:
                            liberties += 1
                            break

        return liberties

    def evaluate(self, board):
        'Function to evaluate how well the agent is doing'

        val = 0
        opp_val = 0
        for i in board:
            for j in i:
                if j!=0:
                    if j==self.player:
                        val += 1
                    else:
                        opp_val += 1

        liberties = self.countLiberties(board, self.player)
        opp_liberties = self.countLiberties(board, 1 if self.player == 2 else 2)
        return val - opp_val + (0.2 * liberties) - (0.2 * opp_liberties) + self.komi

    def hasLiberties(self, board, row, col):
        'Function to judge whether a point has any liberties left'

        player = board[row][col]
        playerGroup = [(row, col)]
        final = []

        while len(playerGroup) != 0:
            n = playerGroup.pop()
            final += [n]
            x = [i for i in self.getNeighbours(n[0], n[1])]

            for i in x:
                if board[i[0]][i[1]] == 0:
                    return True
                if board[i[0]][i[1]] == player and (i[0], i[1]) not in final and (i[0], i[1]) not in playerGroup:
                    playerGroup += [(i[0], i[1])]

        return False

    def removeDeadPieces(self, board):
        'Function to remove dead pieces from the board'

        toRemove = []

        for i in range(5):
            for j in range(5):
                if not self.hasLiberties(board, i , j):
                    toRemove += [(i,j)]

        for point in toRemove:
            board[point[0]][point[1]] = 0

        return board


    def isValid(self, board, i, j, player):
        'Function to check if coin placement is valid'

        temp = deepcopy(board)
        temp[i][j] = player

        #check if this coin has any liberties
        if self.hasLiberties(temp, i, j):
            return True

        #if not, check if neighbouring opponent coin has any liberties
        else:
            #get all neighbours
            neighbours = self.getNeighbours(i, j)

            #find opponents among neighbours
            opponents = [k for k in neighbours if temp[k[0]][k[1]] not in [player, 0]]

            #check whether they have any liberties
            for n in opponents:
                if self.hasLiberties(temp, n[0], n[1]):
                    return False
            return True

    def generateValidMoves(self, board, player, depth):
        'Function to find all possible valid moves'

        possibilities = []

        for i in range(5):
            for j in range(5):
                if board[i][j] == 0 and self.isValid(board, i, j, player):
                    temp = deepcopy(board)
                    temp[i][j] = player
                    temp = self.removeDeadPieces(temp)
                    if depth > 1 or temp != self.past:
                        possibilities += [[temp, [i, j]]]

        return possibilities

    def maxValue(self, board, alpha, beta, depth):
        'Function to maximize points'

        #terminal state test
        if depth == 4 or self.moves + depth == 25:
            return self.evaluate(board), None

        v = float('-inf')
        best_move = None

        for p, m in self.generateValidMoves(board, self.player, depth):

            #go to next level of recursion
            calculated_min, _ = self.minValue(p, alpha, beta, depth+1)
            if calculated_min > v:
                v = calculated_min

            #update alpha and beta
            if v >= beta:
                return v, m     #pruning states
            if v > alpha:
                alpha = v
                best_move = m

        return v, best_move

    def minValue(self, board, alpha, beta, depth):
        'Function to minimize points'

        #terminal state test
        if depth == 4 or self.moves + depth == 25:
            return self.evaluate(board), None

        player = 1 if self.player==2 else 2
        v = float('inf')
        best_move = None

        for p, m in self.generateValidMoves(board, player, depth):
            
            #go to next level of recursion
            calculated_max, _ = self.maxValue(p, alpha, beta, depth+1)
            if calculated_max < v:
                v = calculated_max
            
            #update alpha and beta
            if v <= alpha:    
                return v, m     #pruning states
            if v < beta:
                beta = v
                best_move = m

        return v, best_move

    def miniMax(self, board):
        'Function to drive the minimax algorithm'

        return self.maxValue(board, float('-inf'), float('inf'), 1)

    def analyze(self):
        'Function to analyze the state of the board and make a move'
                
        score, output = self.miniMax(self.current)
        if score > self.score:
            self.skip = False
            self.output = f'{output[0]},{output[1]}'

    def generateOutput(self):
        'Function to generate output file'

        with open('output.txt', 'w') as f:
            if self.skip:
                f.write('PASS')
            else:
                f.write(self.output)
            
            x = {'moves': self.moves + 2}
            json.dump(x, open('misc.json', 'w'))

def main():
    start_time = time.time()
    agent = LittleGo()
    agent.parseInput('test.txt')
    agent.analyze()
    agent.generateOutput()
    print(time.time() - start_time)

main()