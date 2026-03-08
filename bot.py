import time
import random
import logging
import chess

from abc import ABC, abstractmethod
from core.config import Config
from core.vision.vision import ChessboardVision, DesktopVision, RemoteVision
from core.vision.process import Vision2D, Vision3D 
from core.engine import ChessEngine
from core.controller import BoardController, MoveResult
from core.interaction import InteractionManager


logger = logging.getLogger(__name__)

class Bot(ABC):
    INTERFRAME_TIME_S: float = 0.1
    LOST_VISION_TOLERANCE_S: float = 2

    def __init__(self, config: Config):
        self.config = config
        self.scanner: ChessboardVision
        self.running = False
        logger.info(f"Config: {self.config}")

    def mainloop(self, blocking=True) -> None:
        self._reset()

        self.running = True
        while self.running:
            try:
                self._main()
            finally:
                self._wait()
            
            if not blocking:
                break
    
    def stop(self) -> None:
        self.running = False
        self.cleanup()

    def cleanup(self) -> None:
        if hasattr(self, 'scanner'):
            self.scanner.image_source.cleanup()

    def _main(self) -> None:
        self.frame_start_time = time.time()
        self.detected_fen = self._detect_fen()
        
        if not self.detected_fen:
            self._increment_illegal_state()
            return

        if self.is_game_start:
            self._on_game_start()
            return
        
        move_result: MoveResult = self.game.tick(self.detected_fen)

        if move_result == MoveResult.MOVE_DETECTED:
            logger.info(f"Move Detected: \n{self.game.visual_board_repr}")
            best_move = self._get_best_move()
            self._execute_move(best_move)
        elif move_result == MoveResult.ILLEGAL_MOVE:
            self._increment_illegal_state()

    def _detect_fen(self) -> str | None: 
        return self.scanner.get_fen()

    @abstractmethod
    def _execute_move(self, move: str | None) -> None: 
        pass

    def _reset(self) -> None:
        self.engine = ChessEngine(self.config)
        self.game = BoardController()
    
        self.detected_fen: str | None = None
        self.illegal_state_counter: int = 0
        self.is_game_start: bool = True
        self.color: chess.Color | None = None
        self.frame_start_time: float = time.time()
        logger.info("Starting Chess Bot. Looking for board...")        

    def _on_game_start(self) -> None:
        if self.game.set_starting_fen(self.detected_fen):
            self.color = self.player_color
            color_name = "WHITE" if self.color else "BLACK"
            logger.info(f"Bot is {color_name}: {self.detected_fen}")
            logger.info(f"New game initialized. Detected fen from board: {self.detected_fen}")
            self.is_game_start = False
            
            if self.game.board.turn == self.color:
                move = self.engine.get_best_move(self.game.board.fen())
                self._execute_move(move)

    def _wait(self) -> None:
        wait_for = self.INTERFRAME_TIME_S - self.elapsed_frametime_s
        if wait_for > 0:
            time.sleep(wait_for)

    def _get_best_move(self) -> str | None:
        if self.game.board.turn == self.color:
            return self.engine.get_best_move(self.game.board.fen()) if not self.config.play_like_human else self.engine.get_best_move(self.game.board.fen(), self._human_thinking_time_ms)
        return None
    
    def _increment_illegal_state(self) -> None:
        self.illegal_state_counter += 1
        if self.illegal_state_counter > self.allowed_illegal_moves:
            self._handle_too_long_illegal_state()
    
    def _handle_too_long_illegal_state(self) -> None:
        logger.warning("Lost vision or illegal board state...")
        self.illegal_state_counter = 0
        if hasattr(self, 'scanner'):
            c = (self.color == chess.WHITE)
            self.scanner.reset(c)

    @property
    def player_color(self) -> chess.Color:
        return chess.WHITE if self.scanner.player_is_white else chess.BLACK
    
    @property
    def elapsed_frametime_s(self) -> float:
        return time.time() - self.frame_start_time
    
    @property
    def allowed_illegal_moves(self) -> int:
        return int(self.LOST_VISION_TOLERANCE_S/self.INTERFRAME_TIME_S)
    
    @property
    def _human_thinking_time_ms(self) -> int:
        think_for = random.randint(2000,10000) if self.game.board.fullmove_number > 3 else random.randint(1000,4000)
        elapsed_ms = int(self.elapsed_frametime_s*1000)
        return max(think_for - elapsed_ms, 500)


class RemotePhoneBot(Bot):
    def _reset(self) -> None:
        vision_method = Vision3D() if self.config.vision_mode == "3D" else Vision2D()
        source = RemoteVision(self.config, vision_method)
        
        self.scanner = ChessboardVision(source)
        super()._reset()

    def _execute_move(self, move: str | None) -> None:
        pass


class DesktopBot(Bot):
    def _reset(self) -> None:
        vision_method = Vision3D() if self.config.vision_mode == "3D" else Vision2D()
        source = DesktopVision(vision_method)
        
        self.scanner = ChessboardVision(source)
        self.actor = InteractionManager(self.config.play_like_human)
        super()._reset()

    def _execute_move(self, move: str | None) -> None:
        if move:
            logger.info(f"Executing Bot Move: {move}")
            self.actor.execute_move(self.scanner, move)