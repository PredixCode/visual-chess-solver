import io
import re
import os
import logging
import cv2
import numpy as np

from datetime import datetime
from cv2.typing import MatLike
from PIL import Image
from mss import mss
from numpy.typing import NDArray

np.int = int  # type: ignore
from chessimg2pos import predict_fen
from chessimg2pos.chessboard_finder import detect_chessboard_corners

logger = logging.getLogger(__name__)

class Vision2D:
    def __init__(self):
        pass

    def get_fen(self, cropped_board_img: np.ndarray) -> str | None:
        cropped_img_rgb = cv2.cvtColor(cropped_board_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(cropped_img_rgb)
        
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        try:            
            result = predict_fen(image_path=img_byte_arr, output_type="all")
            fen = result.get("fen", None)
            return self._compress_fen(fen) if fen else None
        except Exception as e:
            logger.warning(f"Failed to predict FEN from cropped board.: {e}")
            return None
        
    def _compress_fen(self, fen: str) -> str:
        return re.sub(r'1+', lambda match: str(len(match.group(0))), fen)
    

class Vision3D:
    def __init__(self):
        pass

    def get_fen(self, cropped_board_img: np.ndarray) -> str | None:
        logger.warning("3D Vision get_fen() called but not yet implemented.")
        return None



# Fen Utils
def get_player_color(raw_fen: str | None) -> bool | None:
    """Looks at the top of the fen to determine board orientation."""
    if raw_fen is None:
        return None
    
    first_rank = raw_fen.split('/')[0]
    
    white_pieces = sum(1 for c in first_rank if c.isupper())
    black_pieces = sum(1 for c in first_rank if c.islower())
    
    if white_pieces > black_pieces:
        logger.info("Perspective Autodetected: Playing as BLACK")
        return False
    else:
        logger.info("Perspective Autodetected: Playing as WHITE")
        return True

class ChessboardScanner:
    def __init__(self, active_vision_method: int=0):
        self.sct = mss()
        self.reset()
        self.vision_methods = [Vision2D(), Vision3D()]
        self.active_vision_method: int = active_vision_method
        self.autodetect_vision_method: bool = True

    def reset(self, is_white_at_bottom=None):
        self.is_white_at_bottom = is_white_at_bottom
        self.board_dimensions = None
        self.monitor_offset_x = 0
        self.monitor_offset_y = 0
        self.current_raw_fen = None
        self.active_monitor_idx = None

    @property
    def vision(self): 
        return self.vision_methods[self.active_vision_method]

    @property
    def player_is_white(self) -> bool | None:
        if self.is_white_at_bottom is None:
            self.is_white_at_bottom = get_player_color(self.current_raw_fen)
        return self.is_white_at_bottom
    
    def get_fen(self) -> str | None:
        # 1. Get the raw frame and update board dimensions
        frame = self._get_active_frame()
        if frame is None:
            return None
        
        cropped_frame = self._crop_frame(frame)
        if cropped_frame is None:
            # If cropping fails, window might have moved, reset dimensions
            self.board_dimensions = None 
            return None

        # 3. Process the vision and store result
        fen = self.vision.get_fen(cropped_frame)
        if fen:
            self.current_raw_fen = fen
        return self.current_raw_fen

    def _get_active_frame(self):
        """Handles monitor selection and board localization."""
        if self.active_monitor_idx is not None:
            frame = self._capture(self.active_monitor_idx)
            
            if self.board_dimensions is None:
                self.board_dimensions = self._find_board(frame)
                
            return frame if self.board_dimensions is not None else None

        return self._scan_all_monitors()

    def _scan_all_monitors(self):
        """Iterates through monitors to find and lock onto the chessboard."""
        for i in range(1, len(self.sct.monitors)):
            frame = self._capture(i)
            board_rect = self._find_board(frame)

            if board_rect is not None:
                logger.info(f"Board found on Monitor {i}!")
                self.active_monitor_idx = i
                self.board_dimensions = board_rect
                return frame
                
        return None
    
    def get_square_coordinates(self, square_name: str) -> tuple[int, int]:
        """Calculates exact screen (x,y) pixels for a square."""
        if self.board_dimensions is None:
            raise ValueError("Board not detected yet.")

        x_min, y_min, x_max, y_max = [int(v) for v in self.board_dimensions]
        board_width = x_max - x_min
        board_height = y_max - y_min
        
        square_w = board_width / 8.0
        square_h = board_height / 8.0

        file_idx = ord(square_name[0]) - ord('a')
        rank_idx = int(square_name[1]) - 1 

        if self.player_is_white:
            screen_x_idx = file_idx
            screen_y_idx = 7 - rank_idx
        else:
            screen_x_idx = 7 - file_idx
            screen_y_idx = rank_idx

        # Calculate coordinates relative to the screenshot image
        center_x = x_min + (screen_x_idx * square_w) + (square_w / 2.0)
        center_y = y_min + (screen_y_idx * square_h) + (square_h / 2.0)

        # Add monitor offsets to get absolute screen coordinates for PyAutoGUI
        absolute_x = center_x + self.monitor_offset_x
        absolute_y = center_y + self.monitor_offset_y

        return int(absolute_x), int(absolute_y)
    
    def _capture(self, monitor_idx: int) -> MatLike:
        """Captures a specific monitor rather."""
        monitor = self.sct.monitors[monitor_idx]
        self.monitor_offset_x = monitor["left"]
        self.monitor_offset_y = monitor["top"]
        
        screenshot = np.array(self.sct.grab(monitor))
        return cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

    def _crop_frame(self, frame: MatLike) -> MatLike | None:
        try:
            if self.board_dimensions is not None:
                x_min, y_min, x_max, y_max = [int(v) for v in self.board_dimensions]
                return frame[y_min:y_max, x_min:x_max]
        except Exception as e:
            logger.error(f"Cropping failed: {e}")
            self.board_dimensions = None
        return None

    def _find_board(self, frame: MatLike) -> NDArray | None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        dimensions = detect_chessboard_corners(img_arr_gray=gray)
        
        if dimensions is None:
            return None
        
        logger.info("Chessboard located successfully.")
        return dimensions