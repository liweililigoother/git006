
import random
import math
from flask import Flask, jsonify, render_template, request

class GameBoard:
    def __init__(self):
        self.adj_list = {
            1: [2, 3, 4], 2: [1, 3, 5, 6, 7], 3: [1, 2, 4, 7, 8], 4: [1, 3, 9, 10],
            5: [2, 6, 11], 6: [2, 5, 7, 11], 7: [2, 3, 6, 8, 11, 12], 8: [3, 7, 9, 12],
            9: [4, 8, 10, 12, 13], 10: [4, 9, 13], 11: [5, 6, 7, 12, 14], 12: [7, 8, 9, 11, 13, 14],
            13: [9, 10, 12, 14], 14: [11, 12, 13]
        }
        self.positions = {node: None for node in self.adj_list}
        self.pieces = {
            'O': {2, 5, 6, 7, 11},
            'D': {4, 9, 10, 12, 13}
        }
        for p_type, piece_set in self.pieces.items():
            for p in piece_set:
                self.positions[p] = p_type

    def get_neighbors(self, node):
        return self.adj_list.get(node, [])

    def is_empty(self, node):
        return self.positions.get(node) is None

    def get_piece_at(self, node):
        return self.positions.get(node)

    def move_piece(self, start_node, end_node, player_type):
        if self.get_piece_at(start_node) != player_type:
            return False, "此处无你的棋子。"
        if not self.is_empty(end_node):
            return False, "目标位置已有棋子。"
        if end_node not in self.get_neighbors(start_node):
            return False, "无效移动：目标不是相邻位置。"
        if self.is_suicide_move(start_node, end_node, player_type):
            return False, "无效移动：此为自杀走法。"

        self.positions[end_node] = player_type
        self.positions[start_node] = None
        self.pieces[player_type].remove(start_node)
        self.pieces[player_type].add(end_node)

        opponent_type = 'O' if player_type == 'D' else 'D'
        surrounded = self.find_surrounded_pieces(opponent_type)
        captured_count = 0
        for piece_loc in surrounded:
            if self.remove_piece(piece_loc, opponent_type):
                captured_count += 1
        
        msg = "移动成功。"
        if captured_count > 0:
            msg += f" 提掉 {captured_count} 个对方棋子。"
        return True, msg

    def remove_piece(self, piece_loc, player_type):
        if self.positions.get(piece_loc) == player_type:
            self.positions[piece_loc] = None
            self.pieces[player_type].remove(piece_loc)
            return True
        return False

    def is_suicide_move(self, piece_loc, dest_loc, player_type):
        temp_positions = self.positions.copy()
        temp_positions[dest_loc] = player_type
        temp_positions[piece_loc] = None
        
        for neighbor in self.get_neighbors(dest_loc):
            if temp_positions.get(neighbor) is None:
                return False
        
        opponent_type = 'O' if player_type == 'D' else 'D'
        for neighbor in self.get_neighbors(dest_loc):
            if temp_positions.get(neighbor) == opponent_type:
                is_opponent_surrounded = True
                for opp_neighbor in self.get_neighbors(neighbor):
                    if temp_positions.get(opp_neighbor) is None:
                        is_opponent_surrounded = False
                        break
                if is_opponent_surrounded:
                    return False
        return True

    def get_all_legal_moves(self, player_type):
        legal_moves = []
        for start_node in list(self.pieces[player_type]):
            for end_node in self.get_neighbors(start_node):
                if self.is_empty(end_node) and not self.is_suicide_move(start_node, end_node, player_type):
                    legal_moves.append((start_node, end_node))
        return legal_moves

    def find_surrounded_pieces(self, player_to_check):
        surrounded = []
        for piece_loc in list(self.pieces[player_to_check]):
            if all(not self.is_empty(n) for n in self.get_neighbors(piece_loc)):
                surrounded.append(piece_loc)
        return surrounded

    def check_win_condition(self, current_player, turn_count=0, d_at_center_last_turn=False):
        opponent_player = 'O' if current_player == 'D' else 'D'

        if len(self.pieces[opponent_player]) == 0:
            return current_player, f"{current_player}方提掉所有对方棋子!"
        if not self.get_all_legal_moves(opponent_player):
            return current_player, f"对方无棋可走。{current_player}方获胜!"
        if current_player == 'O' and d_at_center_last_turn and self.get_piece_at(8) == 'D':
            return 'D', "Δ方占领中心一回合! Δ方获胜!"
        if turn_count >= 50:
            return 'O', "O方成功防守50回合! O方获胜!"
        return None, None

class AIPlayer:
    def __init__(self, board, player_type):
        self.board = board
        self.player_type = player_type
        self.opponent_type = 'D' if player_type == 'O' else 'O'

    def make_move(self):
        legal_moves = self.board.get_all_legal_moves(self.player_type)
        if not legal_moves:
            return None

        for move in legal_moves:
            if self._is_capture_move(move):
                return move
        
        if self.player_type == 'O':
            for d_piece in list(self.board.pieces[self.opponent_type]):
                if 8 in self.board.get_neighbors(d_piece) and self.board.is_empty(8):
                    for move in legal_moves:
                        if move[1] == 8:
                            return move

        return random.choice(legal_moves) 
    
    def _is_capture_move(self, move):
        start, end = move
        temp_board = GameBoard()
        temp_board.positions = self.board.positions.copy()
        temp_board.pieces = {k: v.copy() for k, v in self.board.pieces.items()}
        temp_board.move_piece(start, end, self.player_type)
        return len(temp_board.find_surrounded_pieces(self.opponent_type)) > 0

app = Flask(__name__)

game_board = GameBoard()
ai = AIPlayer(game_board, 'O')
current_player = 'D'
turn_count = 0
d_at_center_last_turn = False
game_over = False
winner = None
win_message = ""

# Manually defined node coordinates for the web frontend
node_coords = {
    1: (300, 50), 4: (450, 150), 10: (450, 450), 14: (300, 550),
    11: (150, 450), 5: (150, 150),
    2: (220, 120), 3: (380, 120), 9: (380, 480), 13: (220, 480),
    6: (220, 220), 7: (300, 220), 8: (380, 300), 12: (300, 380)
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gamestate', methods=['GET'])
def gamestate():
    return jsonify({
        'positions': game_board.positions,
        'adj_list': game_board.adj_list,
        'node_coords': node_coords,
        'current_player': current_player,
        'game_over': game_over,
        'winner': winner,
        'win_message': win_message,
        'turn_count': turn_count,
        'message': "欢迎来到圈地博弈！您是 Δ 方 (进攻方)。"
    })

@app.route('/move', methods=['POST'])
def move():
    global current_player, game_over, winner, win_message, turn_count, d_at_center_last_turn

    if game_over:
        return jsonify({'error': '游戏已结束。'}), 400

    if current_player != 'D':
        return jsonify({'error': '不是你的回合。'}), 400

    data = request.json
    start_node = data.get('start')
    end_node = data.get('end')

    if not all(isinstance(i, int) for i in [start_node, end_node]):
        return jsonify({'error': '无效的节点。'}), 400

    success, msg = game_board.move_piece(start_node, end_node, 'D')

    if not success:
        return jsonify({'error': msg}), 400
    
    d_at_center_last_turn = (end_node == 8)
    winner, win_message = game_board.check_win_condition('D', turn_count, d_at_center_last_turn)
    if winner:
        game_over = True
        return jsonify({
            'message': win_message, 
            'game_over': game_over, 
            'winner': winner,
            'positions': game_board.positions
        })

    # AI's turn
    current_player = 'O'
    turn_count += 1
    
    ai_move = ai.make_move()
    ai_msg = ""
    if ai_move:
        ai_start, ai_end = ai_move
        _, ai_msg = game_board.move_piece(ai_start, ai_end, 'O')
    
    winner, win_message = game_board.check_win_condition('O', turn_count, d_at_center_last_turn)
    if winner:
        game_over = True
    else:
        current_player = 'D'

    return jsonify({
        'message': f"你移动: {start_node} 到 {end_node}. {msg} \n电脑移动: {ai_start} 到 {ai_end}. {ai_msg}",
        'game_over': game_over,
        'winner': winner,
        'win_message': win_message,
        'positions': game_board.positions
    })

@app.route('/reset', methods=['POST'])
def reset():
    global game_board, ai, current_player, turn_count, d_at_center_last_turn, game_over, winner, win_message
    game_board = GameBoard()
    ai = AIPlayer(game_board, 'O')
    current_player = 'D'
    turn_count = 0
    d_at_center_last_turn = False
    game_over = False
    winner = None
    win_message = ""
    return jsonify({'message': '游戏已重置。'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
