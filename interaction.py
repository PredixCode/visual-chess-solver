import time
import logging
import pyautogui

from vision import VisionManager



logger = logging.getLogger(__name__)

class InteractionManager:
    def __init__(self):
        pyautogui.PAUSE = 0.05 

    def execute_move(self, vision: VisionManager, uci_move: str):
        """Translates engine UCI (e.g., 'e2e4' or 'e7e8q') to physical mouse clicks."""
        start_sq = uci_move[:2]
        end_sq = uci_move[2:4]
        promotion = uci_move[4:] if len(uci_move) > 4 else None

        try:
            start_pos = vision.get_square_coordinates(start_sq)
            end_pos = vision.get_square_coordinates(end_sq)
            pyautogui.moveTo(*start_pos)
            pyautogui.click()
            time.sleep(0.05)
            pyautogui.moveTo(*end_pos)
            pyautogui.click()
            if promotion:
                # Assumes auto-queen is on, or double clicking target square secures a queen
                time.sleep(0.1)
                pyautogui.click()

        except ValueError as ve:
            logger.error(ve)
