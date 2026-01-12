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
        return True, "Move successful."

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
        # Temporarily perform the move
        original_piece_at_dest = self.positions[dest_loc]
        original_piece_at_start = self.positions[piece_loc]
        
        self.positions[dest_loc] = player_type
        self.positions[piece_loc] = None
        
        # Check if the moved piece (at dest_loc) is now surrounded
        is_suicided = True
        for neighbor in self.get_neighbors(dest_loc):
            if self.is_empty(neighbor):
                is_suicided = False
                break

        # Revert the move
        self.positions[piece_loc] = original_piece_at_start
        self.positions[dest_loc] = original_piece_at_dest
        
        return is_suicided

# Example usage (will be part of main game loop later)
if __name__ == "__main__":
    board = GameBoard()
    print("Initial Board State:")
    board.display()
    print("\nInitial O pieces:", board.pieces['O'])
    print("Initial D pieces:", board.pieces['D'])

    # Test a valid move for D
    print("\n--- Attempting D move from 4 to 3 (valid) ---")
    success, msg = board.move_piece(4, 3, 'D')
    print(msg)
    board.display()
    print("D pieces after move:", board.pieces['D'])

    # Test an invalid move (destination not empty)
    print("\n--- Attempting D move from 3 to 2 (invalid - O piece there) ---")
    success, msg = board.move_piece(3, 2, 'D')
    print(msg)
    board.display()

    # Test suicide move (need to set up a scenario where it would be suicide)
    # For now, manually forcing a situation for testing suicide
    # Let's say D at 9, O at 8, 10, 12, 4 is empty. Moving D from 9 to 4.
    # If 9's other neighbors (8,10,12,13) are filled, and 4's neighbors (1,3,9,10) are filled except 9,
    # then moving 9->4 might be a suicide if 4 is then surrounded.
    
    # Reset for specific suicide test scenario
    board_suicide_test = GameBoard()
    board_suicide_test.positions = {node: None for node in board_suicide_test.adj_list}
    board_suicide_test.pieces = {'O': set(), 'D': set()}
    
    board_suicide_test.positions[1] = 'O'
    board_suicide_test.pieces['O'].add(1)
    board_suicide_test.positions[3] = 'O'
    board_suicide_test.pieces['O'].add(3)
    board_suicide_test.positions[9] = 'D' # Piece to be moved
    board_suicide_test.pieces['D'].add(9)
    board_suicide_test.positions[10] = 'O'
    board_suicide_test.pieces['O'].add(10)

    print("\n--- Suicide Move Test Setup ---")
    board_suicide_test.display()
    print("D piece at 9. O pieces at 1, 3, 10.")
    print("Neighbors of 4 (target for D):", board_suicide_test.get_neighbors(4))
    
    # Try moving D from 9 to 4. If 4's neighbors (1,3,10) are filled, this could be suicide.
    print("\nAttempting D move from 9 to 4...")
    # Check current state of neighbors of 4:
    # 1: O, 3: O, 9: D, 10: O
    # So 4 would be surrounded by O(1), O(3), D(9), O(10)
    # If D moves from 9 to 4, 4 will be surrounded by O(1), O(3), O(10)
    # Since 9 will be empty, it won't be surrounded.
    # Let's make sure 9's other neighbors are filled
    # Need more pieces for a proper suicide test in this setup
    
    # A simpler setup for suicide: Move to a completely blocked spot
    board_suicide_test_simple = GameBoard()
    board_suicide_test_simple.positions = {node: 'O' for node in board_suicide_test_simple.adj_list}
    board_suicide_test_simple.positions[1] = None # Make 1 empty
    board_suicide_test_simple.positions[2] = 'D'  # Place D at 2
    board_suicide_test_simple.positions[3] = 'O'
    board_suicide_test_simple.positions[5] = 'O'
    board_suicide_test_simple.positions[6] = 'O'
    board_suicide_test_simple.positions[7] = 'O'

    board_suicide_test_simple.pieces = {'O': set([n for n in board_suicide_test_simple.adj_list if n != 1 and n != 2]), 'D': set([2])}

    print("\n--- Simple Suicide Test Setup (D at 2, all neighbors of 1 are O except 2) ---")
    board_suicide_test_simple.display()
    print(f"Neighbors of 1: {board_suicide_test_simple.get_neighbors(1)}")
    
    print("\nAttempting D move from 2 to 1 (should be suicide)...")
    success, msg = board_suicide_test_simple.move_piece(2, 1, 'D')
    print(msg)
    board_suicide_test_simple.display()
    print("D pieces after suicide attempt:", board_suicide_test_simple.pieces['D'])
    
    # Test find_surrounded_pieces (need a scenario where an O piece is surrounded)
    board_capture_test = GameBoard()
    board_capture_test.positions = {node: None for node in board_capture_test.adj_list}
    board_capture_test.pieces = {'O': set(), 'D': set()}

    # Place D pieces around O piece at 2
    board_capture_test.positions[1] = 'D'
    board_capture_test.pieces['D'].add(1)
    board_capture_test.positions[3] = 'D'
    board_capture_test.pieces['D'].add(3)
    board_capture_test.positions[5] = 'D'
    board_capture_test.pieces['D'].add(5)
    board_capture_test.positions[6] = 'D'
    board_capture_test.pieces['D'].add(6)
    board_capture_test.positions[7] = 'D'
    board_capture_test.pieces['D'].add(7)
    
    board_capture_test.positions[2] = 'O' # This O piece should be surrounded
    board_capture_test.pieces['O'].add(2)

    print("\n--- Capture Test Setup (O at 2, surrounded by D) ---")
    board_capture_test.display()
    
    surrounded_o = board_capture_test.find_surrounded_pieces('O')
    print(f"Surrounded O pieces: {surrounded_o}")
    if surrounded_o:
        for loc in surrounded_o:
            board_capture_test.remove_piece(loc, 'O')
        print("Removed surrounded O pieces.")
        board_capture_test.display()
        print("O pieces remaining:", board_capture_test.pieces['O'])

