import os
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

from interfaces import CameraControllerInterface


class CameraController(CameraControllerInterface):
    def __init__(self, device_id: int=0):
        self.device_id = device_id
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> bool:
        """カメラデバイスをopenする"""
        logger.info("open関数、実行開始")
        self._cap = cv2.VideoCapture(self.device_id)
        if not self._cap.isOpened():
            logger.error("Error: カメラが開けなかった... 接続を確認!!")
            return False
        return True

    def release(self) -> None:
        """カメラデバイスを解放する"""
        logger.info("release開始")
        if self._cap:
            logger.debug("self._cap発見: release実施")
            self._cap.release()
            self._cap = None
        else:
            logger.debug("self._capが見つからない。スルーする。")

    def is_opened(self) -> bool:
        if self._cap is None:
            return False
        return bool(self._cap.isOpened())

    def set_resolution(self, resolution: tuple[int, int]) -> None:
        """カメラの解像度(幅, 高さ)を設定する。open()済みでないと反映されない"""
        if not self._cap:
            logger.warning("set_resolution: カメラが未openのためスキップします。")
            return
        width, height = resolution
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        logger.info(f"set_resolution: {width}x{height} を設定")

    def capture(self) -> np.ndarray | None:
        """1フレームを撮影して返す"""
        if not self._cap:
            return None
        ret, frame = self._cap.read()
        if ret:
            logger.debug("capture実施")
            return frame
        else:
            return None

    def save_capture(self, frame) -> None:
        if frame is None:
            logger.warning("save_capture: frameがNoneのため保存をスキップします。")
        img_path = self._make_img_path(img_name="capture")
        cv2.imwrite(str(img_path), frame)

    def save_roi_capture(self, frame, roi: tuple[int, int, int, int]) -> None:
        if frame is None or roi is None:
            logger.warning("save_roi_capture: frameまたはroiがNoneのためスキップします。")
        img_path = self._make_img_path(img_name="roi_capture")
        x, y, w, h = roi
        roi_frame = frame[y: y+h, x: x+w]
        cv2.imwrite(str(img_path), roi_frame)
    
    def _make_img_path(self, img_name) -> Path:
        # 実行時のカレントディレクトリに依存しないよう、このファイル基準（usb_camera_adapter/img）に固定する
        img_dir = Path(__file__).resolve().parent.parent.parent / "img"
        os.makedirs(img_dir, exist_ok=True)
        img_path = img_dir / f"{img_name}.png"
        return img_path

    def is_led_on(self, roi: tuple[int, int, int, int], threshold: int) -> bool:
        """指定した領域(ROI)のLEDが点灯しているかを判定する"""
        frame = self.capture()
        if frame is None:
            return False
        x, y, w, h = roi
        roi_frame = frame[y: y+h, x: x+w] 
        gray_roi = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        mean_value = gray_roi.mean()
        if mean_value > threshold:
            logger.info(f"is_led_on/LED_ON/ROI画像の平均({mean_value})と足切り({threshold})")
            return True
        else:
            logger.info(f"is_led_on/LED_OFF/ROI画像の平均({mean_value})と足切り({threshold})")
            return False
