from stockfish import Stockfish

class ChessEngine:
    def __init__(self, path: str, depth: int=25, threads: int=16, thinking_time_in_s: int=2):
        self._engine = Stockfish(path=path, depth=depth)
        self.set_threads(threads)
        self.set_thinking_time(thinking_time_in_s)

    def get_best_move(self, fen: str) -> str | None:
        if not self._engine.is_fen_valid(fen):
            return None
        self._engine.set_fen_position(fen)
        return self._engine.get_best_move()

    def set_threads(self, threads: int) -> None:
        self._engine._set_option("Threads", threads)

    def set_thinking_time(self, time_in_s: int) -> None:
        self._engine._set_option("Minimum Thinking Time", time_in_s)