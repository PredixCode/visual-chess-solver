import os
import json
import logging

from functools import cached_property



logger = logging.getLogger(__name__)

class BotConfig:
    def __init__(self, config_path: str = "config.json"):
        self.file_data = self._read_config(config_path)

    def _read_config(self, config_path) -> dict:
        with open(config_path, "r") as f:
            return json.load(f)
        
    @cached_property
    def base_dir(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))
        
    @cached_property
    def stockfish_path(self):
        return os.path.join(self.base_dir, self.file_data["stockfish_path"])
    
    @cached_property
    def threads(self) -> int:
        try:
            return int(self.file_data["threads"])
        except:
            logger.warning("Amount of threads for stockfish not set in config.json. Defaulting to 4...")
            return 4

    @cached_property
    def depth(self) -> int | None:
        try:
            return int(self.file_data["depth"])
        except Exception:
            return None
        
    @cached_property
    def think_time(self) -> int | None:
        try:
            return int(self.file_data["thinking_time_in_s"])
        except Exception:
            return None
    