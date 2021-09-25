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
        return board[coord[0]][coord[1]] != 0

    def minimax(board, depth, player):
        if player == ME:
            best = [-1, -1, -infinity]
        else:
            best = [-1, -1, +infinity]

        if depth == 0 or game_over(board):
            score = evaluate(board)
            return [-1, -1, score]

        for cell in empty_cells(board):
            x, y = cell[0], cell[1]
            board[x][y] = player # make my move
            score = minimax(board, depth - 1, -player)
            board[x][y] = 0 # return to initial state
            score[0], score[1] = x, y

            if player == ME:
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
    myRole = None
    for event in client.events():
        logging.info(f"Recevied Events. {json.dumps(event.data)}")
        gameEvent = json.loads(event.data)
        # primary move
        if 'youAre' in gameEvent and gameEvent['youAre'] == "O":
            logging.info(f"I am O.")
            myRole = "O"
            board[1][1] = ME
            requests.post(playUrl, data={"action": "putSymbol", "position": "C"})
        elif 'youAre' in gameEvent and gameEvent['youAre'] == "X":
            logging.info(f"I am the second player.")
            continue

        elif 'player' in gameEvent and 'action' in gameEvent:
            if gameEvent['player'] == myRole:
                logging.info("Safely ignored the game news.")
                continue
            if 'position' not in gameEvent:
                logging.info(f"Flip Table.")
                requests.post(playUrl, data={"action": "(╯°□°)╯︵ ┻━┻"})
                break
            boardNewMove = getCoordPos(gameEvent['position'], actionToCoord)
            # Flip Table
            if boardNewMove == (-1, -1) or isInvalidMove(boardNewMove, board):
                logging.info(f"Flip Table.")
                requests.post(playUrl, data={"action": "(╯°□°)╯︵ ┻━┻"})
            else:
                row, col = boardNewMove
                board[row][col] = COMP
                boardForCal = board.copy()
                logging.info(f"Before MiniMax after component moved {board}")
                move = minimax(boardForCal, 9, ME)
                logging.info(f"myNewMove {move}")
                myMove_row, myMove_col = move[0], move[1]
                board[myMove_row][myMove_col] = ME
                logging.info(f"After MiniMax after I moved {board}")
                # update to server
                boardPosStr = getBoardPosStr((myMove_row, myMove_col))
                logging.info({"action": "putSymbol", "position": boardPosStr})
                requests.post(playUrl, data={"action": "putSymbol", "position": boardPosStr})
        elif 'winner' in gameEvent:
            break
            
        else:
            logging.info(f"Unknown incoming response {event.data}")
            requests.post(playUrl, data={"action": "(╯°□°)╯︵ ┻━┻"})
    return json.dumps({'result': "ended"})



