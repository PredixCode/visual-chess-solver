import logging
import os
import time
import chess

from vision import VisionManager
from engine import ChessEngine
from controller import BoardController, TickResult
from interaction import InteractionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def run_bot():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    stockfish_path = os.path.join(base_dir, "stockfish.exe")

    vision = VisionManager()
    engine = ChessEngine(path=stockfish_path, threads=16, thinking_time_in_s=2)
    game = BoardController()
    actor = InteractionManager(vision)

    is_initial_state = True
    bot_color = None # Will be assigned once vision autodetects
    
    logger.info("Starting Chess Solver. Looking for board...")
    
    while True:
        raw_pieces = vision.capture_and_parse()
        
        if not raw_pieces:
            time.sleep(0.1)
            continue

        if is_initial_state:
            # Grab the dynamically detected color from vision
            bot_color = chess.WHITE if vision.is_white_bottom else chess.BLACK
            
            if game.set_starting_fen(raw_pieces):
                logger.info(f"New game initialized. Tracking from: {raw_pieces}")
                is_initial_state = False
                
                if game.board.turn == bot_color:
                    suggestion = engine.get_best_move(game.board.fen())
                    if suggestion:
                        logger.info(f"Executing Initial Engine Move: {suggestion}")
                        actor.execute_move(suggestion)
            continue

        tick_result: TickResult = game.tick(raw_pieces)
        
        if tick_result == TickResult.MOVE_DETECTED:
            logger.info(f"\n{game.visual_board_repr}")
            
            if game.board.turn == bot_color:
                suggestion = engine.get_best_move(game.board.fen())
                if suggestion:
                    logger.info(f"Executing Engine Move: {suggestion}")
                    actor.execute_move(suggestion)

        if tick_result == TickResult.ILLEGAL_MOVE:
            vision.drop_board_position()

        if tick_result == TickResult.NO_MOVE_DETECTED:
            time.sleep(0.1)

if __name__ == "__main__":
    run_bot()