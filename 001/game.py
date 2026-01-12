# game.py

class GameBoard:
    def __init__(self):
        # Define the adjacency list for the game board
        # This includes the user's feedback for connections 1-4 and 14-13
        self.adj_list = {
            1: [2, 3, 4],
            2: [1, 3, 5, 6, 7],
            3: [1, 2, 4, 7, 8],
            4: [1, 3, 9, 10],
            5: [2, 6, 11],
            6: [2, 5, 7, 11],
            7: [2, 3, 6, 8, 11, 12],
            8: [3, 7, 9, 12],  # Center point
            9: [4, 8, 10, 12, 13],
            10: [4, 9, 13],
            11: [5, 6, 7, 12, 14],
            12: [7, 8, 9, 11, 13, 14],
            13: [9, 10, 12, 14],
            14: [11, 12, 13]
        }
        # Initialize positions, None for empty, 'O' for defensive, 'D' for offensive (Delta)
        self.positions = {node: None for node in self.adj_list}

        # Initial piece placements
        # User is Offensive (Delta), AI is Defensive (O)
        # O: (2), (5), (6), (7), (11)
        # D: (4), (9), (10), (12), (13)
        self.pieces = {
            'O': set([2, 5, 6, 7, 11]),
            'D': set([4, 9, 10, 12, 13])
        }

        # Apply initial placements to positions
        for p in self.pieces['O']:
            self.positions[p] = 'O'
        for p in self.pieces['D']:
            self.positions[p] = 'D'

    def display(self):
        # A simple text-based display for now.
        # This can be improved later to be more "circular"
        # Attempting a more structured display based on the general layout
        display_map = {
            1: ' ', 2: ' ', 3: ' ', 4: ' ',
            5: ' ', 6: ' ', 7: ' ', 8: ' ', 9: ' ', 10: ' ',
            11: ' ', 12: ' ', 13: ' ', 14: ' '
        }
        for node in self.positions:
            piece = self.positions[node]
            display_map[node] = piece if piece else ' '

        # Improved ASCII art attempt for a circular layout
        board_str = f"""
        {display_map[1]}-------{display_map[4]}
       / |     | \ 
      {display_map[2]}--{display_map[3]}--{display_map[9]}--{display_map[10]}
     |  / \\ / \\  |
     | {display_map[5]}--{display_map[6]}--{display_map[7]}--{display_map[8]}--{display_map[12]}--{display_map[13]} |
     |  \\ / \\ /  |
      {display_map[11]}-------{display_map[14]}
        """
        print(board_str)


    def get_neighbors(self, node):
        return self.adj_list.get(node, [])

    def is_empty(self, node):
        return self.positions.get(node) is None

    def get_piece_at(self, node):
        return self.positions.get(node)

    def move_piece(self, start_node, end_node, player_type):
        if self.get_piece_at(start_node) != player_type:
            return False, "You don't have a piece at the starting position."
        if not self.is_empty(end_node):
            return False, "The destination is not empty."
        if end_node not in self.get_neighbors(start_node):
            return False, "Invalid move: destination is not a neighbor."
        
        # Check for suicide move before performing
        if self.is_suicide_move(start_node, end_node, player_type):
            return False, "Invalid move: This is a suicide move."

        # Perform the move
        self.positions[end_node] = player_type
        self.positions[start_node] = None
        self.pieces[player_type].remove(start_node)
        self.pieces[player_type].add(end_node)
        
        # After a successful move, check for surrounded opponent pieces
        opponent_type = 'O' if player_type == 'D' else 'D'
        surrounded_opponent_pieces = self.find_surrounded_pieces(opponent_type)
        
        captured_count = 0
        for piece_loc in surrounded_opponent_pieces:
            if self.remove_piece(piece_loc, opponent_type):
                captured_count += 1
        
        if captured_count > 0:
            return True, f"Move successful. Captured {captured_count} opponent piece(s)."
        else:
            return True, "Move successful."

    def get_all_legal_moves(self, player_type):
        legal_moves = []
        for start_node in list(self.pieces[player_type]): # Iterate over a copy as self.pieces might change if we deepcopy
            for end_node in self.get_neighbors(start_node):
                if self.is_empty(end_node):
                    # Temporarily perform the move to check for suicide
                    # Create a deep copy of the board state to test hypothetical moves
                    temp_positions = {k: v for k, v in self.positions.items()}
                    temp_pieces = {'O': set(self.pieces['O']), 'D': set(self.pieces['D'])}

                    temp_positions[end_node] = player_type
                    temp_positions[start_node] = None
                    # Update temp_pieces as well, needed for checking is_surrounded correctly later
                    temp_pieces[player_type].remove(start_node)
                    temp_pieces[player_type].add(end_node)
                    
                    # Check if the moved piece is now surrounded in the temporary state
                    is_suicided = True
                    for neighbor in self.get_neighbors(end_node):
                        # Use temp_positions for checking emptiness
                        if temp_positions.get(neighbor) is None:
                            is_suicided = False
                            break
                    
                    if not is_suicided:
                        legal_moves.append((start_node, end_node))
        return legal_moves

    def check_win_condition(self, current_player, turn_count=0):
        opponent_player = 'O' if current_player == 'D' else 'D'

        # Condition 1: Current player captured all opponent pieces
        if len(self.pieces[opponent_player]) == 0:
            return current_player, f"{current_player} captured all opponent pieces!"

        # Condition 2: Opponent has no legal moves (困毙)
        if len(self.get_all_legal_moves(opponent_player)) == 0:
            return current_player, f"{opponent_player} has no legal moves. {current_player} wins!"

        # Condition 3: Delta occupies center (center node is 8)
        if self.positions[8] == 'D':
            # This rule needs "停留一回合" (stay for one turn).
            # We'll check this in the main game loop, but for now,
            # direct occupation means win for simplicity in this function.
            # In the game loop, a flag would track if D entered 8 last turn.
            return 'D', "Delta occupies the center point (8)! Delta wins!"

        # Condition 4: O survives 50 turns (handled in main game loop)
        # This function won't directly check the 50 turn limit,
        # but the main loop will call it and pass the turn_count.
        # This means if turn_count reaches 50 and D hasn't won yet, O wins.
        if turn_count >= 50 and current_player == 'D': # If it's D's turn and 50 turns have passed
             return 'O', "Defensive (O) survived 50 turns! Defensive (O) wins!"
        if turn_count >= 50 and current_player == 'O': # If it's O's turn and 50 turns have passed
             # O can only win this way if D hasn't won yet.
             # This means if D didn't win on its 50th move, then O automatically wins.
             # So this condition is primarily for the *end* of D's 50th turn.
             pass # Will be handled by the main game loop logic


        return None, None # No win yet

    def find_surrounded_pieces(self, player_to_check):
        surrounded = []
        # Create a copy of the set to iterate over, as the original might be modified
        opponent_pieces_locations = list(self.pieces[player_to_check])
        for piece_loc in opponent_pieces_locations:
            is_surrounded = True
            for neighbor in self.get_neighbors(piece_loc):
                # If any neighbor is empty, the piece is not surrounded
                if self.is_empty(neighbor):
                    is_surrounded = False
                    break
            if is_surrounded:
                surrounded.append(piece_loc)
        return surrounded

    def remove_piece(self, piece_loc, player_type):
        if self.positions[piece_loc] == player_type:
            self.positions[piece_loc] = None
            self.pieces[player_type].remove(piece_loc)
            return True
        return False

    def is_suicide_move(self, piece_loc, dest_loc, player_type):
        """
        Checks if a hypothetical move from piece_loc to dest_loc
        would result in the moved piece being surrounded (suicide).
        """
        # Create a deep copy of the board state to test hypothetical moves
        temp_positions = {k: v for k, v in self.positions.items()}
        
        # Temporarily perform the move on the temporary board
        temp_positions[dest_loc] = player_type
        temp_positions[piece_loc] = None
        
        # Check if the moved piece (at dest_loc) is now surrounded in the temporary state
        is_suicided = True
        for neighbor in self.get_neighbors(dest_loc):
            # Check for emptiness using the temporary positions
            if temp_positions.get(neighbor) is None:
                is_suicided = False
                break
        
        return is_suicided

import random

class AIPlayer:
    def __init__(self, board, player_type):
        self.board = board
        self.player_type = player_type
        self.opponent_type = 'D' if player_type == 'O' else 'O' # Should be 'D' for O, 'O' for D

    def make_move(self):
        legal_moves = self.board.get_all_legal_moves(self.player_type)
        if not legal_moves:
            return None # No moves possible

        # Strategy 1: Prioritize capturing opponent pieces
        for move in legal_moves:
            start_node, end_node = move
            temp_board_state = self._simulate_move_on_board_copy(start_node, end_node, self.player_type)
            surrounded_opponent_pieces = temp_board_state.find_surrounded_pieces(self.opponent_type)
            if len(surrounded_opponent_pieces) > 0:
                return move # Found a capturing move

        # Strategy 2: Block Delta from reaching the center (node 8)
        # If AI is O, check if D can move to 8 next turn.
        if self.player_type == 'O':
            # Check if any D piece is one move away from the center
            for d_piece_loc in self.board.pieces[self.opponent_type]:
                if 8 in self.board.get_neighbors(d_piece_loc) and self.board.is_empty(8):
                    # A D piece could move to 8 next turn. Try to block it.
                    # Find an O piece that can move to 8
                    for move in legal_moves:
                        start_node, end_node = move
                        if end_node == 8:
                            return move # Prioritize moving to 8 to block

        # Strategy 3: Try to prevent opponent captures
        # This is more complex, requiring simulating opponent's next turn.
        # For a simple AI, let's skip this for now.

        # Strategy 4: Make a random valid move
        return random.choice(legal_moves)
    
    def _simulate_move_on_board_copy(self, start_node, end_node, player_type):
        """Helper to create a deep copy of the board and simulate a move."""
        # This creates a completely independent copy for simulation
        temp_board = GameBoard()
        temp_board.positions = {k: v for k, v in self.board.positions.items()}
        temp_board.pieces = {k: set(v) for k, v in self.board.pieces.items()}
        
        # Perform the move on the temporary board
        temp_board.positions[end_node] = player_type
        temp_board.positions[start_node] = None
        temp_board.pieces[player_type].remove(start_node)
        temp_board.pieces[player_type].add(end_node)
        
        return temp_board

def main():

    board = GameBoard()

    player_ai = AIPlayer(board, 'O') # AI plays as O (Defensive)



    current_player = 'D' # User plays as D (Offensive)

    turn_count = 0

    game_over = False

    winner = None

    win_message = ""

    

    # Flag to track if D (player) moved to center (8) in previous turn

    d_at_center_last_turn = False



    print("--- 圈地博弈 (Circle of Battle) ---")

    print(f"你扮演: {current_player} (进攻方)")

    print(f"电脑扮演: {player_ai.player_type} (防守方)")

    print("目标: Δ占领中心或吃掉所有O; O阻止Δ占领中心或吃掉所有Δ.")

    print("输入 'quit' 退出游戏。")



    while not game_over:

        turn_count += 1

        print(f"\n--- 回合 {turn_count} ---")

        board.display()

        print(f"当前玩家: {current_player} 棋子: {board.pieces[current_player]}")

        print(f"对手玩家: {'O' if current_player == 'D' else 'D'} 棋子: {board.pieces['O' if current_player == 'D' else 'D']}")



        # Check win condition at the start of the turn (for 'no legal moves')

        # Check if D occupied center for one turn (specifically if O plays and D is still there)

        if current_player == 'O' and d_at_center_last_turn and board.get_piece_at(8) == 'D':

            winner = 'D'

            win_message = "Delta occupied the center point (8) for one turn! Delta wins!"

            game_over = True

            break

        d_at_center_last_turn = False # Reset for this turn



        # Check other win conditions

        winner, win_message = board.check_win_condition(current_player, turn_count)

        if winner:

            game_over = True

            break



        if current_player == 'D': # Human player's turn

            valid_move = False

            while not valid_move:

                try:

                    player_input = input("请输入你的移动 (例如: 4 3, 从4移动到3): ").strip()

                    if player_input.lower() == 'quit':

                        print("游戏结束。")

                        return



                    start_node, end_node = map(int, player_input.split())

                    success, msg = board.move_piece(start_node, end_node, current_player)

                    if success:

                        valid_move = True

                        print(msg)

                        # Check if D moved to center 8

                        if end_node == 8:

                            d_at_center_last_turn = True

                    else:

                        print(f"无效移动: {msg}. 请重试。")

                except ValueError:

                    print("输入格式错误。请按照 '起始位置 目标位置' 的格式输入。")

                except Exception as e:

                    print(f"发生错误: {e}")



        else: # AI player's turn

            print("电脑 (O) 正在思考...")

            ai_move = player_ai.make_move()

            if ai_move:

                start_node, end_node = ai_move

                success, msg = board.move_piece(start_node, end_node, current_player)

                print(f"电脑移动: 从 {start_node} 到 {end_node}. {msg}")

            else:

                # This case should be caught by check_win_condition (no legal moves)

                print("电脑 (O) 没有合法移动。")

                game_over = True # Should be handled by check_win_condition

                break



        # Switch player

        current_player = 'O' if current_player == 'D' else 'D'



    # Game Over

    print("\n--- 游戏结束 ---")

    board.display()

    if winner:

        print(f"恭喜 {winner} 获胜！ {win_message}")

    else:

        print("游戏结束，没有明确的赢家（例如，可能遇到僵局）。")



if __name__ == "__main__":

    main()


