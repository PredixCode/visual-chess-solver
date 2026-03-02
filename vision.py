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

class VisionManager:
    def __init__(self, debug_dir: str = "captured_boards"):
        self.sct = mss()
        self.reset()

    def reset(self):
        self.board_rect = None
        self.is_white_at_bottom = None
        self.monitor_offset_x = 0
        self.monitor_offset_y = 0
        self.current_raw_fen = None
        self.active_monitor_idx = None

    @property
    def player_is_white(self) -> bool | None:
        if self.is_white_at_bottom is None:
            self.is_white_at_bottom = self.get_player_color(self.current_raw_fen)
        return self.is_white_at_bottom

    def get_player_color(self, raw_fen: str | None) -> bool | None:
        """Looks at the top of the image to determine board orientation."""
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

    def get_fen(self) -> str | None:
        frame = None
        # 1. If we are locked onto a specific monitor, only capture that one
        if self.active_monitor_idx is not None:
            frame = self._capture(self.active_monitor_idx)
            
            if self.board_rect is None:
                self.board_rect = self._find_board(frame)
                
            if self.board_rect is None:
                return None
                
            cropped_frame = self._crop_frame(frame)
            if cropped_frame is None:
                return None
                
        # 2. If we don't know the monitor, scan all available individual screens
        else:
            found = False
            # Start at 1 to skip monitors[0] (the stitched multi-monitor bounding box)
            for i in range(1, len(self.sct.monitors)):
                frame = self._capture(i)
                board_rect = self._find_board(frame)
                
                if board_rect is not None:
                    logger.info(f"Board found on Monitor {i}!")
                    self.active_monitor_idx = i
                    self.board_rect = board_rect
                    found = True
                    break
            
            if not found or frame is None:
                return None # Board not found on any monitor
                
            cropped_frame = self._crop_frame(frame)
            if cropped_frame is None:
                return None

        # 3. Predict FEN from the successfully cropped board
        fen = self._predict_fen_from_image(cropped_frame)
        if fen is None:
            return None
        
        self.current_raw_fen = fen
        return fen
    
    def get_square_coordinates(self, square_name: str) -> tuple[int, int]:
        """Calculates exact screen (x,y) pixels for a square, handling perspective and multi-monitor setups."""
        if self.board_rect is None:
            raise ValueError("Board not detected yet.")

        x_min, y_min, x_max, y_max = [int(v) for v in self.board_rect]
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
            if self.board_rect is not None:
                x_min, y_min, x_max, y_max = [int(v) for v in self.board_rect]
                return frame[y_min:y_max, x_min:x_max]
        except Exception as e:
            logger.error(f"Cropping failed: {e}")
            self.board_rect = None
        return None

    def _find_board(self, frame: MatLike) -> NDArray | None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        dimensions = detect_chessboard_corners(img_arr_gray=gray)
        
        if dimensions is None:
            return None
        
        logger.info("Chessboard located successfully.")
        return dimensions
        

    def _predict_fen_from_image(self, img: np.ndarray) -> str | None:
        cropped_img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
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
        if not fen:
            return fen
        return re.sub(r'1+', lambda match: str(len(match.group(0))), fen)