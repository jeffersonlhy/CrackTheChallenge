import logging
import json
import heapq

from flask import request, jsonify

from codeitsuisse import app

logger = logging.getLogger(__name__)

@app.route('/stock-hunter', methods=['POST'])
def stock_hunter():
    class PriorityQueue:
        """
        Implements a priority queue data structure. Each inserted item
        has a priority associated with it and the client is usually interested
        in quick retrieval of the lowest-priority item in the queue. This
        data structure allows O(1) access to the lowest-priority item.

        Note that this PriorityQueue does not allow you to change the priority
        of an item.  However, you may insert the same item multiple times with
        different priorities.
        """
        def  __init__(self):
            self.heap = []
            self.count = 0

        def push(self, item, priority):
            # FIXME: restored old behaviour to check against old results better
            # FIXED: restored to stable behaviour
            entry = (priority, self.count, item)
            # entry = (priority, item)
            heapq.heappush(self.heap, entry)
            self.count += 1

        def pop(self):
            (_, _, item) = heapq.heappop(self.heap)
            #  (_, item) = heapq.heappop(self.heap)
            return item

        def isEmpty(self):
            return len(self.heap) == 0

    def getPossibleMove(board, coord):
        x, y = coord[0], coord[1]
        x_limit = len(board)
        y_limit = len(board[0])
        preList = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
        afterList = []
        for count, pMove in enumerate(preList):
            x1, y1 = pMove[0], pMove[1]
            if x1 >= 0 and y1 >= 0 and x1 < x_limit and y1 < y_limit:
                afterList.append((x1, y1))
        return afterList

    rawdata = request.get_json()
    output = []
    cost = 0
    logging.info(f"received {rawdata}")
    # RISK_LEVEL = ['L', 'M', 'S']
    for data in rawdata:

        board_risk = []
        board_level = []
        board_dp = []
        for i in range(data['targetPoint']['first'] + 1):
            widthList = []
            widthLevel = []
            for j in range(data['targetPoint']['second'] + 1):
                widthLevel.append(0)
                widthList.append([0, False])
            board_risk.append(widthList)
            board_level.append(widthLevel)
            board_dp.append(widthLevel)

        entry_col = data['entryPoint']['first']
        entry_row = data['entryPoint']['second']
        target_col = data['targetPoint']['first']
        target_row = data['targetPoint']['second']

        board_risk[entry_row][entry_col][1] = True
        board_risk[target_row][target_col][1] = True

        gridDepth = data['gridDepth']
        gridKey = data['gridKey']
        hztStep = data['horizontalStepper']
        vtlStep = data['verticalStepper']

        board_level[entry_row][entry_col] = gridDepth % gridKey
        board_level[target_row][target_col] = gridDepth % gridKey

        # risk index
        for x, fst_row_cell in enumerate(board_risk[0]):
            if not fst_row_cell[1]:
                fst_row_cell[0] = x * hztStep
                board_level[0][x] = ((x * hztStep) + gridDepth) % gridKey

        # risk index
        for y, row in enumerate(board_risk):
            if not row[0][1]:
                row[0][0] = y * vtlStep
                board_level[y][0] = ((y * vtlStep) + gridDepth) % gridKey


        for y, row in enumerate(board_risk[1:]):
            for x, cell_risk in enumerate(row[1:]):
                if not cell_risk[1]:
                    cell_risk[0] = board_level[y][x+1] * board_level[y+1][x]
                    board_level[y+1][x+1] = (cell_risk[0] + gridDepth) % gridKey


        # print(board_risk)
        # print(board_level)
        board_cost = []
        board_astar = []
        board_prettify = []

        for row in board_level:
            base = []
            base_astart= []
            base_prettify = []
            for cell in row:
                level = cell%3
                base.append(level)
                if level == 0:
                    base_astart.append(3)
                    base_prettify.append("L")
                elif level == 1:
                    base_astart.append(2)
                    base_prettify.append("M")
                elif level == 2:
                    base_astart.append(1)
                    base_prettify.append("S")
            board_astar.append(base_astart)
            board_prettify.append(base_prettify)
            board_cost.append(base)



        queue = PriorityQueue()
        expanded = set()
        initState = ((entry_row, entry_col), 0)
        queue.push(initState, 0)


        while (not queue.isEmpty()):
            currPosition, accumulated = queue.pop()
            if currPosition == (target_row, target_col):
                cost = accumulated
                break
            if (currPosition not in expanded):
                expanded.add(currPosition)
                succNodes = getPossibleMove(board_astar, currPosition)
                for nextPos in succNodes:
                    x1, y1 = nextPos[0], nextPos[1]
                    queue.push((nextPos, accumulated + board_astar[y1][x1]), accumulated + board_astar[y1][x1])

        output.append({
            "gridMap": json.dumps(board_prettify),
            "minimumCost": cost
        })
    logging.info(json.dumps(output))
    return json.dumps(output)

            