import logging
import cv2
import numpy as np

from abc import ABC, abstractmethod
from mss import mss
from cv2.typing import MatLike


from core.config import Config
from core.vision.process import Vision2D, Vision3D


logger = logging.getLogger(__name__)

class VisionSource(ABC):
    def __init__(self, vision_method: Vision2D|Vision3D):
        self.vision_method = vision_method
        self.board_dimensions = None
        self.monitor_offset_x = 0
        self.monitor_offset_y = 0

    def _process_frame(self, frame: MatLike) -> MatLike | None:
        if self.board_dimensions is None:
            self.board_dimensions = self.vision_method.find_board(frame)

        cropped_frame = self.vision_method.crop_frame(frame, self.board_dimensions)
        if cropped_frame is None:
            self.board_dimensions = None 
            return None
        return cropped_frame


class DesktopVision(VisionSource):
    def __init__(self, vision_method: Vision2D|Vision3D) -> None:
        super().__init__(vision_method)
        self.sct = mss()
        self.active_monitor_idx = None

    def get_frame(self) -> MatLike | None:
        if self.active_monitor_idx is not None:
            frame = self._capture(self.active_monitor_idx)
            cropped_frame = self._process_frame(frame) 
            return cropped_frame if self.board_dimensions is not None else None

        return self._scan_all_monitors()
    
    def _capture(self, monitor_idx: int) -> MatLike:
        monitor = self.sct.monitors[monitor_idx]
        self.monitor_offset_x = monitor["left"]
        self.monitor_offset_y = monitor["top"]
        
        screenshot = np.array(self.sct.grab(monitor))
        return cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    
    def _scan_all_monitors(self):
        for i in range(1, len(self.sct.monitors)):
            frame = self._capture(i)
            board_rect = self.vision_method.find_board(frame)

            if board_rect is not None:
                logger.info(f"Board found on Monitor {i}!")
                self.active_monitor_idx = i
                self.board_dimensions = board_rect
                return self.vision_method.crop_frame(frame, board_rect)
                
        return None

    def cleanup(self):
        self.sct.close()


class RemoteVision(VisionSource):
    def __init__(self, config: Config, vision_method: Vision2D|Vision3D, show_stream:bool = True) -> None:
        super().__init__(vision_method)
        self.show_stream = show_stream

        self.cap = cv2.VideoCapture(config.phone_stream_url)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self.cap.isOpened():
            print("Error: Could not open the stream. Check your URL and Wi-Fi connection.")
            exit()

    def get_frame(self, raw_stream=True) -> MatLike | None:
        ret, frame = self.cap.read()

        if not ret:
            logger.warning("Failed to grab frame. Stream might have ended.")
            return None
        
        if raw_stream:
            self._show_stream(frame)
        
        cropped_frame = self._process_frame(frame)
        if cropped_frame is not None and not raw_stream:
            self._show_stream(cropped_frame)
            
        return cropped_frame

    def cleanup(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()

    def _show_stream(self, frame: MatLike):
        if self.show_stream:
            cv2.imshow('Phone Screen Stream', frame)
            cv2.waitKey(1)