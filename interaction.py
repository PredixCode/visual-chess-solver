import time
import logging
import pyautogui

from human_mouse import MouseController

from vision import ChessboardScanner



logger = logging.getLogger(__name__)

class InteractionManager:
    def __init__(self, play_like_human):
        pyautogui.PAUSE = 0.05
        self.mouse = MouseController()
        self.play_like_human: bool = play_like_human

    def execute_move(self, vision: ChessboardScanner, uci_move: str, ):
        """Translates engine UCI (e.g., 'e2e4' or 'e7e8q') to physical mouse clicks."""
        start_sq = uci_move[:2]
        end_sq = uci_move[2:4]
        promotion = uci_move[4:] if len(uci_move) > 4 else None

        try:
            start_pos = vision.get_square_coordinates(start_sq)
            end_pos = vision.get_square_coordinates(end_sq)

            self._move_mouse(start_pos)
            pyautogui.click()
            time.sleep(0.05)
            self._move_mouse(end_pos)
            pyautogui.click()
            if promotion:
                # Assumes auto-queen is on, or double clicking target square secures a queen
                time.sleep(0.1)
                pyautogui.click()

        except ValueError as ve:
            logger.error(ve)

    def _move_mouse(self, pos: tuple[int, int]):
        if self.play_like_human:
            #self.mouse.move(pos[0], pos[1]) DOESNT WORK
            pyautogui.moveTo(*pos)
        else:
            pyautogui.moveTo(*pos)
