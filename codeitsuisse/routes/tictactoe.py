from math import inf as infinity
import logging
import json
import requests
import sseclient


from flask import request, jsonify

from codeitsuisse import app

logger = logging.getLogger(__name__)

@app.route('/tic-tac-toe', methods=['POST'])
def evaluateTic():
    # Global setup
    ME = -1
    COMP = +1

    board = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]

    actionToCoord = {
        'NW': (0, 0),
        'N': (0, 1),
        'NE': (0, 2),
        'W': (1, 0),
        'C': (1, 1),
        'E': (1, 2),
        'SW': (2, 0),
        'S': (2, 1),
        'SE': (2, 2)
    }

    def getBoardPosStr(coord):
        if coord == (0, 0):
            return 'NW'
        elif coord == (0, 1):
            return 'N'
        elif coord == (0, 2):
            return 'NE'
        elif coord == (1, 0):
            return 'W'
        elif coord == (1, 1):
            return 'C'
        elif coord == (1, 2):
            return 'E'
        elif coord == (2, 0):
            return 'SW'
        elif coord == (2, 1):
            return 'S'
        elif coord == (2, 2):
            return 'SE'
        else:
            return 'Invalid'


    def getCoordPos(direction, actionToCoord):
        try:
            t = actionToCoord[direction]
            return t
        except:
            return (-1, -1)

    def game_over(state):
        """
        This function test if the human or computer wins
        :param state: the state of the current board
        :return: True if the human or computer wins
        """
        return wins(state, ME) or wins(state, COMP)

    def wins(board, player):
        """
        This function tests if a specific player wins. Possibilities:
        * Three rows    [X X X] or [O O O]
        * Three cols    [X X X] or [O O O]
        * Two diagonals [X X X] or [O O O]
        :param board: the board of the current board
        :param player: a human or a computer
        :return: True if the player wins
        """
        win_board = [
            [board[0][0], board[0][1], board[0][2]],
            [board[1][0], board[1][1], board[1][2]],
            [board[2][0], board[2][1], board[2][2]],
            [board[0][0], board[1][0], board[2][0]],
            [board[0][1], board[1][1], board[2][1]],
            [board[0][2], board[1][2], board[2][2]],
            [board[0][0], board[1][1], board[2][2]],
            [board[2][0], board[1][1], board[0][2]],
        ]
        if [player, player, player] in win_board:
            return True
        else:
            return False

    def evaluate(board):
        if wins(board, ME):
            return 1
        elif wins(board, COMP):
            return -1
        else:
            return 0

    def empty_cells(state):
        """
        Each empty cell will be added into cells' list
        :param state: the state of the current board
        :return: a list of empty cells
        """
        cells = []

        for x, row in enumerate(state):
            for y, cell in enumerate(row):
                if cell == 0:
                    cells.append((x, y))

        return cells

    def isInvalidMove(coord, board):
        return board[coord[0], coord[1]] != 0

    def minimax(board, depth, player):
        if player == COMP:
            best = [-1, -1, -infinity]
        else:
            best = [-1, -1, +infinity]

        if depth == 0 or game_over(board):
            score = evaluate(board)
            return [-1, -1, score]

        for cell in empty_cells(board):
            x, y = cell[0], cell[1]
            board[x][y] = player
            score = minimax(board, depth - 1, -player)
            board[x][y] = 0
            score[0], score[1] = x, y

            if player == COMP:
                if score[2] > best[2]:
                    best = score  # max value
            else:
                if score[2] < best[2]:
                    best = score  # min value

        return best


    battleId_raw = request.get_json()
    battleId = battleId_raw['battleId']
    logging.info(f"session_id={battleId}")
    startUrl = f"https://cis2021-arena.herokuapp.com/tic-tac-toe/start/{battleId}"
    playUrl = f"https://cis2021-arena.herokuapp.com/tic-tac-toe/play/{battleId}"
    logging.info(f"sending get request to ={startUrl}")
    response = requests.get(startUrl, stream=True, params={'Accept': 'text/event-stream', 'Connection': 'keep-alive'})
    client = sseclient.SSEClient(response)
    for event in client.events():
        logging.info(f"Recevied Events. {json.dumps(event.data)}")
        gameEvent = json.loads(event.data)
        # primary move
        if 'youAre' in gameEvent and gameEvent['youAre'] == "O":
            logging.info(f"I am O.")
            initmove = {
                "action": "putSymbol",
                "position": "C"
            }
            requests.post(playUrl, data=json.dumps(initmove))
        elif 'youAre' in gameEvent and gameEvent['youAre'] == "X":
            logging.info(f"I am the second player.")
            continue

        elif 'player' in gameEvent and 'action' in gameEvent and 'position' in gameEvent:
            boardNewMove = getCoordPos(gameEvent['position'], actionToCoord)
            # Flip Table
            if boardNewMove == (-1, -1) or isInvalidMove(boardNewMove):
                logging.info(f"Flip Table.")
                requests.post(playUrl, data=json.dumps({"action": "(╯°□°)╯︵ ┻━┻"}))
            else:
                row, col = boardNewMove
                board[row][col] = COMP
                boardForCal = board.copy()
                move = minimax(boardForCal, 8, ME)
                myMove_row, myMove_col = move[0], move[1]
                board[myMove_row][myMove_col] = ME
                # update to server
                boardPosStr = getBoardPosStr((myMove_row, myMove_col))
                logging.info(f"Sending response. Position: {boardPosStr}")
                requests.post(playUrl, data=json.dumps({"action": "putSymbol", "position": boardPosStr}))
        elif 'winner' in gameEvent:
            break
            
        else:
            logging.info(f"Unknown incoming response {event.data}")
    return json.dumps({'result': "ended"})



