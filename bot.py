import logging
import time
import chess

from config import BotConfig
from vision import VisionManager
from engine import ChessEngine
from controller import BoardController, TickResult
from interaction import InteractionManager



logger = logging.getLogger(__name__)

class ChessBot:
    INTERFRAME_TIME: float = 0.1

    def __init__(self, config: BotConfig):
        self.config = config
        self._reset_state()

    def _reset_state(self) -> None:
        self.vision = VisionManager()
        self.engine = ChessEngine(self.config)
        self.game = BoardController()
        self.actor = InteractionManager()

        self.is_game_start = True
        self.color = None
        logger.info("Starting Chess Bot. Looking for board...")

    def mainloop(self) -> None:
        while True:
            raw_pieces = self.vision.get_fen()
            
            if not raw_pieces:
                time.sleep(self.INTERFRAME_TIME)
                continue

            if self.is_game_start:
                # Grab the dynamically detected color from vision
                self.color = chess.WHITE if self.vision.is_white_bottom else chess.BLACK
                
                if self.game.set_starting_fen(raw_pieces):
                    logger.info(f"New game initialized. Tracking from: {raw_pieces}")
                    self.is_game_start = False
                    
                    if self.game.board.turn == self.color:
                        suggestion = self.engine.get_best_move(self.game.board.fen())
                        if suggestion:
                            logger.info(f"Executing Initial Engine Move: {suggestion}")
                            self.actor.execute_move(self.vision, suggestion)
                continue

            tick_result: TickResult = self.game.tick(raw_pieces)
            
            if tick_result == TickResult.MOVE_DETECTED:
                logger.info(f"\n{self.game.visual_board_repr}")
                
                if self.game.board.turn == self.color:
                    suggestion = self.engine.get_best_move(self.game.board.fen())
                    if suggestion:
                        logger.info(f"Executing Engine Move: {suggestion}")
                        self.actor.execute_move(self.vision, suggestion)

            if tick_result == TickResult.ILLEGAL_MOVE:
                self.vision.drop_board_position()

            if tick_result == TickResult.NO_MOVE_DETECTED:
                time.sleep(self.INTERFRAME_TIME)