import os
import json
import logging

from functools import cached_property

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path # Save path as an instance variable
        self.file_data = self._read_config(config_path)

    def _read_config(self, config_path) -> dict:
        with open(config_path, "r") as f:
            return json.load(f)

    def persist(self) -> None:
        """Writes current file_data to disk and clears cached properties to force a reload."""
        with open(self.config_path, "w") as f:
            json.dump(self.file_data, f, indent=4)
        
        # Clear the cached properties so they re-evaluate on the next call
        for key in list(self.__dict__.keys()):
            if key not in ["config_path", "file_data"]:
                del self.__dict__[key]
        
        logger.info("Configuration persisted and cache cleared.")

    # Bot Config
    @cached_property
    def bot_config(self) -> dict:
        return self.file_data.get("bot", {})

    @cached_property
    def mode(self) -> str:
        return self.bot_config.get("mode", "Desktop")
    
    @cached_property
    def vision_mode(self) -> str:
        return self.bot_config.get("vision_mode", "2D")

    @cached_property
    def move_pieces(self) -> bool:
        return bool(self.bot_config.get("move_pieces", False))
    
    @cached_property
    def play_like_human(self) -> bool:
        return bool(self.bot_config.get("play_like_human", False))
    
    @cached_property
    def phone_stream_url(self) -> str:
        return self.bot_config["phone"].get("stream_url", "")
    
    # Stockfish Config
    @cached_property
    def stockfish_config(self) -> dict:
        return self.file_data.get("stockfish", {})    
    
    @cached_property
    def stockfish_path(self) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, self.stockfish_config["path"])
    
    @cached_property
    def threads(self) -> int:
        try:
            return int(self.stockfish_config["threads"])
        except:
            logger.warning("Amount of 'threads' for stockfish not set in 'config.json'. Defaulting to max available...")
            max_threads = os.cpu_count()
            if max_threads:
                logger.info(f"Using '{max_threads}' threads for stockfish.")
                return max_threads
        logger.error("Couldnt find available thread count of CPU, defaulting to '1'.")
        return 1

    @cached_property
    def depth(self) -> int | None:
        try:
            return int(self.stockfish_config["depth"])
        except Exception:
            return None
        
    @cached_property
    def think_time(self) -> int | None:
        try:
            return min(int(self.stockfish_config["thinking_time_in_ms"]), 5000)
        except Exception:
            return None
        
    @cached_property
    def elo(self) -> int | None:
        try:
            return int(self.stockfish_config["elo"])
        except Exception:
            return None
        
    def __str__(self) -> str:
        lines = [
            f"\n|{8*'─'} CONFIGURATION {8*'─'}│",
            f"├──┬ Bot Settings:",
            f"│  ├─ Mode: {self.mode}",
            f"│  ├─ Vision Mode: {self.vision_mode}",
            f"│  ├─ Move Pieces: {self.move_pieces}",
            f"│  ├─ Play Like Human: {self.play_like_human}",
            f"│  └─ Phone Stream URL: {self.phone_stream_url}",
            f"│──┬ Stockfish Settings:",
            f"│  ├─ Path: {self.stockfish_path}",
            f"│  ├─ Threads: {self.threads}",
            f"│  ├─ ELO Rating: {self.elo}",
            f"│  ├─ Depth: {self.depth}",
            f"│  └─ Think Time: {self.think_time}ms",            
            f"│{31*'─'}│\n"
        ]
        return "\n".join(lines)
    
if __name__ == "__main__":
    print(str(Config()))