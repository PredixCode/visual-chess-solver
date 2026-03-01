import chess
import logging

from enum import Enum

class TickResult(Enum):
    NO_MOVE_DETECTED = 1
    MOVE_DETECTED = 2
    ILLEGAL_MOVE = 3


logger = logging.getLogger(__name__)

class BoardController:
    def __init__(self):
        self.board = chess.Board()
        self.last_confirmed_pieces = ""

    def set_starting_fen(self, pieces_fen: str) -> bool:
        """Initializes the backend board to match the screen's starting state."""
        full_fen = f"{pieces_fen} w KQkq - 0 1"
        try:
            self.board.set_fen(full_fen)
            self.last_confirmed_pieces = pieces_fen
            return True
        except ValueError as e:
            logger.error(f"Invalid starting FEN provided: {e}")
            return False

    def tick(self, detected_pieces: str) -> TickResult:
        """
        Pushes legal moves to see if any result in the newly detected vision FEN.
        """
        detected_pieces = detected_pieces.strip().split(" ")[0]
        if detected_pieces == self.last_confirmed_pieces:
            return TickResult.NO_MOVE_DETECTED

        for move in self.board.legal_moves:
            self.board.push(move)
            if self.board.fen().split(" ")[0] == detected_pieces:
                logger.info(f"Move Detected: {move.uci()}")
                self.last_confirmed_pieces = detected_pieces
                return TickResult.MOVE_DETECTED
                
            self.board.pop()

        return TickResult.ILLEGAL_MOVE
    
    @property
    def visual_board_repr(self) -> str:
        symbols = {
            "r": "♖", "n": "♘", "b": "♗", "q": "♕", "k": "♔", "p": "♙",
            "R": "♜", "N": "♞", "B": "♝", "Q": "♛", "K": "♚", "P": "♟",
            None: " "
        }

        # Constants for scaling
        cell_width = 5  # Total width of one square
        horizontal_line = "  +" + ("-" * cell_width + "+") * 8
        
        output = []
        output.append("     a     b     c     d     e     f     g     h")
        output.append(horizontal_line)

        # Iterate through ranks from 8 down to 1
        for rank in range(7, -1, -1):
            row_str = f"{rank + 1} |"
            for file in range(8):
                square = chess.square(file, rank)
                piece = self.board.piece_at(square)
                symbol = symbols[piece.symbol()] if piece else " "
                
                # Center the piece symbol within the cell width
                row_str += f"  {symbol}  |"
            
            output.append(row_str)
            output.append(horizontal_line)

        return "\n".join(output)