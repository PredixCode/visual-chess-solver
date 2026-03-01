import time
import logging
import chess

import random

from config import Config
from vision import VisionManager
from engine import ChessEngine
from controller import BoardController, MoveResult
from interaction import InteractionManager



logger = logging.getLogger(__name__)

class ChessBot:
    INTERFRAME_TIME: float = 0.1
    LOST_VISION_TIME: float = 2

    def __init__(self, config: Config):
        self.config = config
        logger.info(f"Config: {self.config}")
        self._reset()

    def mainloop(self) -> None:
        illegal_move_counter = 0
        while True:
            try:
                self.frame_start_time = time.time()
                detected_fen = self.vision.get_fen()
                
                if not detected_fen:
                    continue

                if self.is_game_start:
                    self._on_game_start(detected_fen)
                    continue

                move_result: MoveResult = self.game.tick(detected_fen)
                
                if move_result == MoveResult.MOVE_DETECTED:
                    self._handle_move()
                elif move_result == MoveResult.ILLEGAL_MOVE:
                    illegal_move_counter += 1
                    if illegal_move_counter > self.allowed_illegal_moves:
                        self._handle_to_many_illegal_moves()
                        illegal_move_counter = 0
            finally:
                self._wait()

    @property
    def elapsed_frametime_s(self) -> float:
        return time.time() - self.frame_start_time
    
    @property
    def allowed_illegal_moves(self) -> int:
        return int(self.LOST_VISION_TIME/self.INTERFRAME_TIME)

    def _reset(self) -> None:
        self.vision = VisionManager()
        self.engine = ChessEngine(self.config)
        self.game = BoardController()
        self.actor = InteractionManager(self.config.play_like_human)

        self.is_game_start = True
        self.color = None
        self.frame_start_time = time.time()
        logger.info("Starting Chess Bot. Looking for board...")

    def _on_game_start(self, fen) -> None:
        # Grab the dynamically detected color from vision
        self.color = chess.WHITE if self.vision.is_white_bottom else chess.BLACK
        
        if self.game.set_starting_fen(fen):
            logger.info(f"New game initialized. Tracking from: {fen}")
            self.is_game_start = False
            
            if self.game.board.turn == self.color:
                suggestion = self.engine.get_best_move(self.game.board.fen())
                if suggestion:
                    logger.info(f"Executing Initial Engine Move: {suggestion}")
                    self.actor.execute_move(self.vision, suggestion)

    def _handle_move(self):
        logger.info(f"Move Detected: \n{self.game.visual_board_repr}")
        if self.game.board.turn == self.color:
            suggestion = self.engine.get_best_move(self.game.board.fen()) if not self.config.play_like_human else self.engine.get_best_move(self.game.board.fen(), self._human_thinking_time_ms())

            if suggestion:
                logger.info(f"Executing Engine Move: {suggestion}")
                self.actor.execute_move(self.vision, suggestion)

    def _wait(self) -> None:
        wait_for = self.INTERFRAME_TIME - self.elapsed_frametime_s
        if wait_for > 0:
            time.sleep(wait_for)

    def _handle_to_many_illegal_moves(self) -> None:
        logger.warning("Lost vision of board...")
        self.vision = VisionManager()

    def _human_thinking_time_ms(self) -> int:
        think_for = random.randint(2000,10000) if self.game.board.fullmove_number > 3 else random.randint(1000,4000)
        elapsed_ms = int(self.elapsed_frametime_s*1000)
        return max(think_for - elapsed_ms, 500)