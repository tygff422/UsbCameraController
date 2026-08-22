from pathlib import Path
from unittest.mock import MagicMock, create_autospec
from camera_controller.camera_controller import CameraController
from interfaces import CameraControllerInterface
from loguru import logger
import numpy as np


class CameraMockController(CameraControllerInterface):
    def __init__(self, device_id: int = 0, auto_open: bool = False, auto_led: bool = False):
        self.device_id = device_id
        self._is_opened: bool = auto_open
        self._led_status: bool = auto_led
        self.resolution: tuple[int, int] | None = None

    def open(self) -> bool:
        self._is_opened = True
        return True

    def release(self) -> None:
        self._is_opened = False

    def is_opened(self) -> bool:
        return self._is_opened

    def capture(self) -> np.ndarray | None:
        if not self._is_opened:
            return None
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        return dummy_frame

    def save_capture(self, frame) -> Path | None:
        logger.debug("save_captureが呼び出されました。(実機を持たないFakeのためファイル保存はスキップ)")
        return None

    def set_led_status(self, status=True) -> None:
        self._led_status = status

    def is_led_on(self, roi: tuple[int, int, int, int], threshold: int) -> bool:
        if not self._is_opened:
            return False
        logger.info(f"is_led_on判定結果 ({self._led_status}) を返却")
        return self._led_status

    def set_resolution(self, resolution: tuple[int, int]) -> None:
        # 実機を持たないFakeなので、呼ばれたことだけ記録する
        self.resolution = resolution
