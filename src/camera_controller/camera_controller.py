import os
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

from interfaces import CameraControllerInterface


class CameraController(CameraControllerInterface):
    def __init__(self, device_id: int = 0, img_dir: str | Path | None = None):
        """img_dir: 撮影画像の保存先を上書きしたい場合に指定する。
        未指定なら従来通り自パッケージ内（usb_camera_adapter/img）に保存する。
        """
        self.device_id = device_id
        self._img_dir = Path(img_dir) if img_dir is not None else None
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

    def save_capture(self, frame) -> Path | None:
        """撮影したframeを画像ファイルとして保存する。実行ごとにタイムスタンプ付きファイル名で残す
        （固定ファイル名だと毎回上書きされ、履歴が残らないため。01_docs/decisions/13参照）。"""
        if frame is None:
            logger.warning("save_capture: frameがNoneのため保存をスキップします。")
            return None
        img_path = self._make_img_path(img_name="capture")
        cv2.imwrite(str(img_path), frame)
        return img_path

    def save_roi_capture(self, frame, roi: tuple[int, int, int, int]) -> Path | None:
        if frame is None or roi is None:
            logger.warning("save_roi_capture: frameまたはroiがNoneのためスキップします。")
            return None
        img_path = self._make_img_path(img_name="roi_capture")
        x, y, w, h = roi
        roi_frame = frame[y: y+h, x: x+w]
        cv2.imwrite(str(img_path), roi_frame)
        return img_path

    def _make_img_path(self, img_name) -> Path:
        # img_dir未指定なら、実行時のカレントディレクトリに依存しないよう
        # このファイル基準（usb_camera_adapter/img）に固定する（後方互換のデフォルト）
        img_dir = self._img_dir or (Path(__file__).resolve().parent.parent.parent / "img")
        os.makedirs(img_dir, exist_ok=True)
        # ミリ秒まで含め、同一実行内での複数回撮影でもファイル名が衝突しないようにする
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        img_path = img_dir / f"{img_name}_{timestamp}.png"
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
