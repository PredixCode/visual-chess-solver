import logging

from core.vision.source import DesktopVision, RemoteVision



logger = logging.getLogger(__name__)

class ChessboardVision:
    def __init__(self, image_source: DesktopVision | RemoteVision):
        self.image_source = image_source
        self.reset()

    def reset(self, is_white_at_bottom=None):
        self.is_white_at_bottom = is_white_at_bottom
        self.current_raw_fen = None

    @property
    def player_is_white(self) -> bool | None:
        if self.is_white_at_bottom is None:
            self.is_white_at_bottom = self._get_player_color()
        return self.is_white_at_bottom
    
    def get_fen(self) -> str | None:
        cropped_frame = self.image_source.get_frame()
        if cropped_frame is None:
            return None

        fen = self.image_source.vision_method.get_fen(cropped_frame)
        if fen:
            self.current_raw_fen = fen
        return self.current_raw_fen

    def get_square_coordinates(self, square_name: str) -> tuple[int, int]:
        dims = self.image_source.board_dimensions
        if dims is None:
            raise ValueError("Board not detected yet.")

        x_min, y_min, x_max, y_max = [int(v) for v in dims]
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

        center_x = x_min + (screen_x_idx * square_w) + (square_w / 2.0)
        center_y = y_min + (screen_y_idx * square_h) + (square_h / 2.0)

        absolute_x = center_x + self.image_source.monitor_offset_x
        absolute_y = center_y + self.image_source.monitor_offset_y

        return int(absolute_x), int(absolute_y)
    
    def _get_player_color(self) -> bool | None:
        if self.current_raw_fen is None:
            return None
        
        first_rank = self.current_raw_fen.split('/')[0]
        white_pieces = sum(1 for c in first_rank if c.isupper())
        black_pieces = sum(1 for c in first_rank if c.islower())
        
        if white_pieces > black_pieces:
            logger.info("Perspective Autodetected: Playing as BLACK")
            return False
        else:
            logger.info("Perspective Autodetected: Playing as WHITE")
            return True