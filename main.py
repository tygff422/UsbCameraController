import cv2
import numpy as np
from loguru import logger

class CameraController:
    def __init__(self, device_id: int=0):
        self.device_id = device_id
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> bool:
        """カメラデバイスをopenする"""
        logger.info("open関数、実行開始")
        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            logger.error("Error: カメラが開けなかった... 接続を確認!!")
            return False
        return True

    def release(self) -> None:
        """カメラデバイスを解放する"""
        logger.info("release開始")
        if self._cap:
            self._cap.release()

    def capture(self) -> np.ndarray | None:
        """1フレームを撮影して返す"""
        ret, frame = self._cap.read()
        if ret:
            logger.debug(frame)
            return frame
        else:
            return None

    def save_capture(self, frame):
        cv2.imwrite("test.png", frame)
        pass

    def is_led_on(self, roi: tuple[int, int, int, int], threshold: int) -> bool:
        """指定した領域(ROI)のLEDが点灯しているかを判定する"""
        pass


camera = CameraController()
camera.open()
frame = camera.capture()
camera.save_capture(frame)
camera.release()


