# game.py
import tkinter as tk
from tkinter import messagebox
import random
import math

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
        
        # Check if this move captures any opponent pieces
        opponent_type = 'O' if player_type == 'D' else 'D'
        for neighbor in self.get_neighbors(dest_loc):
            if temp_positions.get(neighbor) == opponent_type:
                # Is the neighboring opponent piece surrounded now?
                is_opponent_surrounded = True
                for opp_neighbor in self.get_neighbors(neighbor):
                    if temp_positions.get(opp_neighbor) is None:
                        is_opponent_surrounded = False
                        break
                if is_opponent_surrounded:
                    return False # Not a suicide if it captures.
        return True

    def get_all_legal_moves(self, player_type):
        legal_moves = []
        for start_node in self.pieces[player_type]:
            for end_node in self.get_neighbors(start_node):
                if self.is_empty(end_node) and not self.is_suicide_move(start_node, end_node, player_type):
                    legal_moves.append((start_node, end_node))
        return legal_moves

    def find_surrounded_pieces(self, player_to_check):
        surrounded = []
        for piece_loc in self.pieces[player_to_check]:
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

        # Strategy 1: Capture opponent
        for move in legal_moves:
            if self._is_capture_move(move):
                return move
        
        # Strategy 2: Block center
        if self.player_type == 'O':
            for d_piece in self.board.pieces[self.opponent_type]:
                if 8 in self.board.get_neighbors(d_piece) and self.board.is_empty(8):
                    for move in legal_moves:
                        if move[1] == 8:
                            return move

        # Strategy 3: Random move
        return random.choice(legal_moves)
    
    def _is_capture_move(self, move):
        start, end = move
        temp_board = GameBoard()
        temp_board.positions = self.board.positions.copy()
        temp_board.pieces = {k: v.copy() for k, v in self.board.pieces.items()}
        temp_board.move_piece(start, end, self.player_type)
        return len(temp_board.find_surrounded_pieces(self.opponent_type)) > 0


class GameGUI(tk.Tk):
    def __init__(self, board):
        super().__init__()
        self.title("圈地博弈")
        self.board = board
        self.ai = AIPlayer(self.board, 'O')
        self.current_player = 'D'
        self.turn_count = 0
        self.d_at_center_last_turn = False
        self.selected_piece_node = None
        self.game_over = False

        # --- Style ---
        self.WOOD_COLOR = "#DEB887" # BurlyWood
        self.DARK_WOOD_COLOR = "#A0522D" # Sienna
        self.LIGHT_WOOD_COLOR = "#F5DEB3" # Wheat
        self.PIECE_RADIUS = 20
        self.NODE_RADIUS = 5

        # --- Layout ---
        self.canvas = tk.Canvas(self, width=600, height=600, bg=self.WOOD_COLOR)
        self.canvas.pack()
        self.status_label = tk.Label(self, text="欢迎来到圈地博弈！您是 Δ 方 (进攻方)。", font=("Arial", 14), pady=10)
        self.status_label.pack()
        
        self.node_coords = self._setup_node_coords(600, 600)
        self.canvas.bind("<Button-1>", self.on_board_click)
        
        self.draw_board()

    def _setup_node_coords(self, width, height):
        center_x, center_y = width / 2, height / 2
        outer_r = width / 2 - 50
        mid_r = width / 2 - 150
        inner_r = width / 2 - 250
        
        coords = {
            1: (center_x, center_y - outer_r),
            2: (center_x - mid_r, center_y - inner_r),
            3: (center_x, center_y - inner_r),
            4: (center_x, center_y - outer_r + 100), # Manually adjust for layout
            5: (center_x - outer_r, center_y),
            6: (center_x - inner_r, center_y),
            7: (center_x - inner_r, center_y - inner_r),
            8: (center_x, center_y), # Center
            9: (center_x, center_y + inner_r),
            10: (center_x, center_y + outer_r - 100), # Manually adjust
            11: (center_x - mid_r, center_y + inner_r),
            12: (center_x + inner_r, center_y),
            13: (center_x + mid_r, center_y + inner_r),
            14: (center_x + outer_r, center_y),
        }
        # A more symmetrical layout
        coords = {
            8: (center_x, center_y),
            3: (center_x, center_y - 100),
            7: (center_x - 50, center_y - 50),
            12: (center_x + 50, center_y),
            9: (center_x, center_y + 100),
            
            2: (center_x - 100, center_y - 100),
            6: (center_x - 150, center_y),
            11: (center_x - 100, center_y + 100),
            13: (center_x + 100, center_y + 100),
            
            1: (center_x, center_y - 200),
            4: (center_x, center_y - 150),
            5: (center_x - 200, center_y),
            10: (center_x, center_y + 150),
            14: (center_x + 200, center_y),
        }
        # Final adjustment for better circular shape
        coords = {
             1: (300, 50),  4: (450, 150), 10: (450, 450), 14: (300, 550),
            11: (150, 450),  5: (150, 150),
             2: (220, 120),  3: (380, 120),  9: (380, 480), 13: (220, 480),
             6: (220, 220),  7: (300, 220),  8: (380, 300), 12: (300, 380)
        }
        return coords


    def draw_board(self):
        self.canvas.delete("all")
        # Draw connections
        for start_node, neighbors in self.board.adj_list.items():
            for end_node in neighbors:
                if start_node < end_node:
                    x1, y1 = self.node_coords[start_node]
                    x2, y2 = self.node_coords[end_node]
                    self.canvas.create_line(x1, y1, x2, y2, fill=self.DARK_WOOD_COLOR, width=3)
        
        # Draw nodes and pieces
        for node, coord in self.node_coords.items():
            x, y = coord
            # Draw node circle
            self.canvas.create_oval(x - self.NODE_RADIUS, y - self.NODE_RADIUS,
                                    x + self.NODE_RADIUS, y + self.NODE_RADIUS,
                                    fill=self.WOOD_COLOR, outline=self.DARK_WOOD_COLOR)
            
            piece = self.board.get_piece_at(node)
            if piece:
                color = self.DARK_WOOD_COLOR if piece == 'D' else self.LIGHT_WOOD_COLOR
                outline_color = self.LIGHT_WOOD_COLOR if piece == 'D' else self.DARK_WOOD_COLOR
                
                self.canvas.create_oval(x - self.PIECE_RADIUS, y - self.PIECE_RADIUS,
                                        x + self.PIECE_RADIUS, y + self.PIECE_RADIUS,
                                        fill=color, outline=outline_color, width=2)
                
                text = 'Δ' if piece == 'D' else 'O'
                self.canvas.create_text(x, y, text=text, font=("Arial", 16, "bold"), fill=outline_color)

            # Draw node number
            self.canvas.create_text(x, y + self.PIECE_RADIUS + 10, text=str(node), font=("Arial", 10), fill="black")

        if self.selected_piece_node:
            x, y = self.node_coords[self.selected_piece_node]
            self.canvas.create_oval(x - self.PIECE_RADIUS, y - self.PIECE_RADIUS,
                                    x + self.PIECE_RADIUS, y + self.PIECE_RADIUS,
                                    outline="blue", width=3)

    def on_board_click(self, event):
        if self.game_over or self.current_player != 'D':
            return
            
        node = self.get_node_at_pos(event.x, event.y)
        if not node:
            return

        if not self.selected_piece_node:
            if self.board.get_piece_at(node) == self.current_player:
                self.selected_piece_node = node
                self.update_status(f"选中棋子 at {node}. 请点击目标位置。")
        else:
            start_node = self.selected_piece_node
            end_node = node
            self.selected_piece_node = None
            
            success, msg = self.board.move_piece(start_node, end_node, self.current_player)
            self.update_status(msg)
            
            if success:
                self.d_at_center_last_turn = (end_node == 8)
                self.end_player_turn()

        self.draw_board()

    def end_player_turn(self):
        self.draw_board()
        winner, win_message = self.board.check_win_condition(self.current_player, self.turn_count, self.d_at_center_last_turn)
        if winner:
            self.handle_game_over(winner, win_message)
            return

        self.current_player = 'O'
        self.turn_count += 1
        self.update_status(f"回合 {self.turn_count}: 电脑 (O) 正在思考...")
        self.after(500, self.ai_turn) # Give a small delay for user to see their move

    def ai_turn(self):
        if self.game_over: return

        winner, win_message = self.board.check_win_condition(self.current_player, self.turn_count, self.d_at_center_last_turn)
        if winner:
            self.handle_game_over(winner, win_message)
            return
            
        move = self.ai.make_move()
        if move:
            start, end = move
            _, msg = self.board.move_piece(start, end, self.current_player)
            self.update_status(f"电脑移动: 从 {start} 到 {end}. {msg}")
        else:
            # This should be caught by win condition check, but as a fallback
            self.handle_game_over(self.current_player, "电脑无棋可走!")
            return

        self.draw_board()
        
        winner, win_message = self.board.check_win_condition(self.current_player, self.turn_count, self.d_at_center_last_turn)
        if winner:
            self.handle_game_over(winner, win_message)
            return

        self.current_player = 'D'
        self.update_status(f"回合 {self.turn_count+1}: 到你了 (Δ).")

    def handle_game_over(self, winner, message):
        self.game_over = True
        self.update_status(f"游戏结束! {message}")
        messagebox.showinfo("游戏结束", message)

    def get_node_at_pos(self, x, y):
        for node, coord in self.node_coords.items():
            dist = math.sqrt((x - coord[0])**2 + (y - coord[1])**2)
            if dist <= self.PIECE_RADIUS:
                return node
        return None

    def update_status(self, text):
        self.status_label.config(text=text)

def main():
    game_board = GameBoard()
    app = GameGUI(game_board)
    app.mainloop()

if __name__ == "__main__":
    main()