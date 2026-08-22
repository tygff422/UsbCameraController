from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np


class CameraControllerInterface(ABC):
    @abstractmethod
    def open(self) -> bool:
        pass

    @abstractmethod
    def release(self) -> None:
        pass

    @abstractmethod
    def is_opened(self) -> bool:
        pass

    @abstractmethod
    def capture(self) -> np.ndarray | None:
        pass

    @abstractmethod
    def save_capture(self, frame) -> Path | None:
        """frameを画像ファイルとして保存し、保存先パスを返す。保存しなかった場合はNone。"""
        pass

    @abstractmethod
    def is_led_on(self, roi: tuple[int, int, int, int], threshold: int) -> bool:
        pass

    @abstractmethod
    def set_resolution(self, resolution: tuple[int, int]) -> None:
        pass
