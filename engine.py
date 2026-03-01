from stockfish import Stockfish
from config import BotConfig

class ChessEngine:
    def __init__(self, config: BotConfig):
        if config.depth:
            self._engine = Stockfish(path=config.stockfish_path, depth=config.depth)
        else:
            self._engine = Stockfish(path=config.stockfish_path)
        if config.threads:
            self.set_threads(config.threads)
        if config.think_time:
            self.set_thinking_time(config.think_time)

    def get_best_move(self, fen: str) -> str | None:
        if not self._engine.is_fen_valid(fen):
            return None
        self._engine.set_fen_position(fen)
        return self._engine.get_best_move()

    def set_threads(self, threads: int) -> None:
        self._engine._set_option("Threads", threads)

    def set_thinking_time(self, time_in_s: int) -> None:
        self._engine._set_option("Minimum Thinking Time", time_in_s)