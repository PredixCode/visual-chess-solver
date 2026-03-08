import io
import re
import logging
import cv2
import numpy as np

from cv2.typing import MatLike
from PIL import Image
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
        
    def find_board(self, frame: MatLike) -> NDArray | None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        dimensions = detect_chessboard_corners(img_arr_gray=gray)
        
        if dimensions is None:
            return None
        
        logger.info("Chessboard located successfully.")
        return dimensions
    
    def crop_frame(self, frame: MatLike, board_dimensions) -> MatLike | None:
        try:
            if board_dimensions is not None:
                x_min, y_min, x_max, y_max = [int(v) for v in board_dimensions]
                return frame[y_min:y_max, x_min:x_max]
            return None
        except Exception as e:
            logger.error(f"Cropping failed: {e}")
        return None
        
    def _compress_fen(self, fen: str) -> str:
        return re.sub(r'1+', lambda match: str(len(match.group(0))), fen)
    

class Vision3D:
    def __init__(self):
        pass

    def get_fen(self, cropped_board_img: np.ndarray) -> str | None:
        logger.warning("3D Vision get_fen() called but not yet implemented.")
        return None
    
    def find_board(self, frame: MatLike) -> NDArray | None:
        logger.warning("3D Vision find_board() called but not yet implemented.")
        return None
    
    def crop_frame(self, frame: MatLike, board_dimensions) -> MatLike | None:
        logger.warning("3D Vision crop_frame() called but not yet implemented.")
        return None