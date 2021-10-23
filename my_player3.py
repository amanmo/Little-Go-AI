from copy import deepcopy
import json
import math
import pickle
import random
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
            self.history = []
        elif count == 1:
            self.moves = 1
            self.history = []
        else:
            data = json.load(open('misc.json'))
            self.moves = data['moves']
            self.history = data['history']

        flag = False
        for i in range(5):
            for j in range(5):
                if self.past[i][j] == 0 and self.current[i][j] != 0:
                    self.history = [[self.boardToString(self.past), str(i) + str(j), 1 if self.player == 2 else 2]] + self.history
                    flag  = True
                    break
            if flag:
                break

        
        self.score = self.calcScore(self.current, self.player)

    def calcScore(self, board, player):
        'Function to calculate score of a player'

        score = 0 if player == 1 else 2.5
        for i in range(5):
            for j in range(5):
                if board[i][j] == player:
                    score += 1

        return score

    def getNeighbours(self, i, j):
        'Function to return all neighbours of a point'

        neighbours = []

        if i>0: neighbours += [(i-1, j)]
        if i<4: neighbours += [(i+1, j)]
        if j>0: neighbours += [(i, j-1)]
        if j<4: neighbours += [(i, j+1)]

        return neighbours

    def countLiberties(self, board, player):
        'Function to count total number of liberties for a player'

        liberties = []

        for i in range(5):
            for j in range(5):
                if board[i][j] == player:
                    liberties += [k for k in self.getNeighbours(i, j) if board[k[0]][k[1]]==0 and k not in liberties]

        return len(liberties)

    def getGroup(self, board, row, col, visited):
        'Function to find the group of a player'

        playerGroup = [(row, col)]
        player = board[row][col]
        visited[row][col] = True
        group = []

        while len(playerGroup) != 0:
            n = playerGroup.pop()
            visited[n[0]][n[1]] = True
            group += [n]

            for k in self.getNeighbours(n[0], n[1]):
                if board[k[0]][k[1]] == player and (k[0], k[1]) not in group and (k[0], k[1]) not in playerGroup:
                    playerGroup += [(k[0], k[1])]

        return group, visited

    def getGroupLiberty(self, board, groups, player):
        'Function to find liberty of a set of groups'

        groupLiberties = []
        for group in groups:
            liberties = []
            for i, j in group:
                if board[i][j] == player:
                    liberties += [k for k in self.getNeighbours(i, j) if board[k[0]][k[1]]==0 and k not in liberties]
            groupLiberties += [liberties]

        return groupLiberties


    # def findBiggestGroup(self, board, player):
    #     'Function to find the biggest group belonging to a player'

    #     visited = [[False for _ in range(5)] for _ in range(5)]
    #     maxSize = 0
    #     for i in range(5):
    #         for j in range(5):
    #             if board[i][j] == player and not visited[i][j]:
    #                 group, visited = self.getGroup(board, i, j, visited)
    #                 maxSize = max(maxSize, len(group))

    #     return maxSize

    def evaluate(self, board, moves):
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

        if moves == 0:
            return val - opp_val + self.komi

        liberties = self.countLiberties(board, self.player)
        opp_liberties = self.countLiberties(board, 1 if self.player == 2 else 2)

        # groupSize = self.findBiggestGroup(board, self.player)
        # opp_groupSize = self.findBiggestGroup(board, 1 if self.player == 2 else 2)

        return val - opp_val + (0.5 * ((liberties - opp_liberties) / moves)) + self.komi #+ (0.4 * ((groupSize - opp_groupSize) / moves))

    def hasLiberties(self, board, row, col):
        'Function to judge whether a point has any liberties left'

        player = board[row][col]
        playerGroup = [(row, col)]
        final = []

        while len(playerGroup) != 0:
            n = playerGroup.pop()
            final += [n]

            for i in self.getNeighbours(n[0], n[1]):
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

        return board, len(toRemove)


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
                    temp, _ = self.removeDeadPieces(temp)
                    if depth > 1 or temp != self.past:
                        possibilities += [[temp, [i, j]]]

        return possibilities

    def terminalStateTest(self, depth):

        return (self.moves < 11 and depth == 4) or (depth == 6) or (self.moves + depth >= 25)

    def maxValue(self, board, alpha, beta, depth):
        'Function to maximize points'

        #terminal state test
        if self.terminalStateTest(depth):
            return self.evaluate(board, self.moves + depth), None

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
        if self.terminalStateTest(depth):
            return self.evaluate(board, self.moves + depth), None

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

    def greedyCheck(self):
        'Function to look for an opponent group with 1 remaining liberty'

        opp = 1 if self.player == 2 else 2
        visited = [[False for _ in range(5)] for _ in range(5)]
        groups = []

        for i in range(5):
            for j in range(5):
                if self.current[i][j] == opp and not visited[i][j]:
                    group, visited = self.getGroup(self.current, i, j, visited)
                    groups += [group]

        groupLiberties = self.getGroupLiberty(self.current, groups, opp)

        flag = False
        max = 0
        best_move = None

        for i in range(len(groups)):
            if len(groupLiberties[i]) == 1:
                move = groupLiberties[i][0]
                temp = deepcopy(self.current)
                if self.isValid(self.current, move[0], move[1], self.player):
                    temp = deepcopy(self.current)
                    temp[move[0]][move[1]] = self.player
                    temp, pieces = self.removeDeadPieces(temp)
                    if temp != self.past and pieces > max:
                        flag = True
                        max = pieces
                        best_move = move
                
        return flag, best_move

    def boardToString(self, board):
        'Function to convert board to string'

        x = ''
        for i in board:
            for j in i:
                x += str(j)
        return x

    def analyze(self):
        'Function to analyze the state of the board and make a move'

        #manually surround central point
        if self.moves < 5:
            plus = [(1,2), (2,1), (2,3), (3,2)]
            i = random.choice(plus)
            while self.current[i[0]][i[1]] != 0:
                plus.remove(i)
                i = random.choice(plus)
            self.skip = False
            self.output = i
            return

        else:
            #Step 1: Greedy Check
            flag, output = self.greedyCheck()
            if flag:
                self.skip = False
                self.output = output
                return
                
            #Step 2: Q value check
            Q = pickle.load(open('Q_table.txt', 'rb'))
            state = self.boardToString(self.current)
            if state in Q:
                best_action = None
                extreme_q = float('-inf') if self.player == 1 else float('inf')
                for action in Q[state]:
                    if (self.player == 1 and Q[state][action] > extreme_q) or (self.player == 2 and Q[state][action] < extreme_q):
                        extreme_q = Q[state][action]
                        best_action = action

                if (math.fabs(Q[state][best_action]) > 0.1):
                    self.skip = False
                    self.output = (int(best_action[0]), int(best_action[1]))
                    return

        #Step 3: MiniMax with Alpha Beta
        _, output = self.miniMax(self.current)
        temp = deepcopy(self.current)
        temp[output[0]][output[1]] = self.player
        score = self.calcScore(temp, self.player)
        if score >= self.score:
            self.skip = False
            self.output = output

    def generateOutput(self):
        'Function to generate output file'

        with open('output.txt', 'w') as f:
            if self.skip:
                f.write('PASS')
            else:
                f.write(f'{self.output[0]}, {self.output[1]}')
            
            x = {'moves': self.moves + 2, 'history': [[self.boardToString(self.current), str(self.output[0]) + str(self.output[1]), self.player]] + self.history}
            json.dump(x, open('misc.json', 'w'))

def main():
    start_time = time.time()
    agent = LittleGo()
    agent.parseInput()
    agent.analyze()
    agent.generateOutput()
    print(time.time() - start_time)

main()