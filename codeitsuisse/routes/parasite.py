import logging
import json

from flask import request, jsonify

from codeitsuisse import app

logger = logging.getLogger(__name__)

@app.route('/parasite', methods=['POST'])
def parasite():
    class Queue:
        "A container with a first-in-first-out (FIFO) queuing policy."
        def __init__(self):
            self.list = []

        def push(self,item):
            "Enqueue the 'item' into the queue"
            self.list.insert(0,item)

        def pop(self):
            """
            Dequeue the earliest enqueued item still in the queue. This
            operation removes the item from the queue.
            """
            return self.list.pop()

        def isEmpty(self):
            "Returns true if the queue is empty"
            return len(self.list) == 0

    def getPossibleMove(board, coord):
        x, y = coord[0], coord[1]
        x_limit = len(board)
        y_limit = len(board[0])
        preList = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
        afterList = []
        for pMove in preList:
            x1, y1 = pMove[0], pMove[1]
            if x1 >= 0 and y1 >= 0 and x1 < x_limit and y1 < y_limit:
                afterList.append((x1, y1))
        return afterList

    def isSurrounded(board, coord):
        # row, col = coord[0], coord[1]
        successors = getPossibleMove(board, coord)
        return all(board[cod[0]][cod[1]] == 0 for cod in successors)

    def isInfected(board, coord):
        return board[coord[0]][coord[1]] == 3

    def isVacantPlace(board, coord):
        return board[coord[0]][coord[1]] == 0

    def isVaccinated(board, coord):
        return board[coord[0]][coord[1]] == 2

    def searchForClosestInfected(board, coord):
        expanded = set()
        queue = Queue()
        queue.push((coord, 0))

        while (not queue.isEmpty()):
            curPos, curCount = queue.pop()
            row, col = curPos[0], curPos[1]
            if board[row][col] == 3:
                return curCount
            if curPos not in expanded:
                expanded.add(curPos)
                succList = getPossibleMove(board, (row, col))
                successors = filter(lambda x: board[x[0]][x[1]] == 1 or board[x[0]][x[1]] == 3, succList)
                for succNode in successors:
                    queue.push((succNode, curCount+1))
        
        return -1

    output = []
    data = request.get_json()
    for case in data:
        room_no = case['room']
        board = case['grid']
        targets = case['interestedIndividuals']
        case_output = {
            'room': room_no,
            "p1": {},
            "p2": 0,
            "p3": 0,
            "p4": 0
        }
        for target in targets:
            coord = target.split(',')
            coordinate = (int(coord[0]), int(coord[1]))
            if isSurrounded(board, coordinate) or isInfected(board, coordinate) or isVacantPlace(board, coordinate) or isVaccinated(board, coordinate):
                case_output['p1'][target] = -1
                continue
            turnNeeded = searchForClosestInfected(board, coordinate)
            case_output['p1'][target] = turnNeeded if turnNeeded != -1 else -1

        output.append(case_output)

    logging.info(output)
    return json.dumps(output)
