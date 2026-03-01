from stockfish import Stockfish
from config import Config

class ChessEngine:
    def __init__(self, config: Config):
        self.config = config
        if config.depth:
            self._engine = Stockfish(path=config.stockfish_path, depth=config.depth)
        else:
            self._engine = Stockfish(path=config.stockfish_path)
        if config.threads:
            self.set_threads(config.threads)

    def get_best_move(self, fen: str, time_in_ms: int | None = None) -> str | None:
        if not self._engine.is_fen_valid(fen):
            return None
        self._engine.set_fen_position(fen)
        if time_in_ms:
            return self._engine.get_best_move_time(time=time_in_ms)
        elif self.config.think_time:
            return self._engine.get_best_move_time(time=self.config.think_time)
        return self._engine.get_best_move()

    def set_threads(self, threads: int) -> None:
        self._engine._set_option("Threads", threads)