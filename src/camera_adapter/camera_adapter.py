import asyncio
from typing import Any, Dict

from loguru import logger
import numpy as np
from camera_controller.camera_controller import CameraController
from adapter_core.baseadapter import BaseAdapter


class CameraAdapter(BaseAdapter):
    def __init__(self, config: Dict[str, Any] | None = None, camera_controller=None):
        if camera_controller is not None:
            self.camera_controller = camera_controller
        else:
            device_id = (config or {}).get("device_id", 0)
            self.camera_controller = CameraController(device_id=device_id)
        self._roi = (100, 150, 50, 50)
        self._threshold = 70
    
    def setup(self) -> bool:
        """カメラの初期化と準備状態の確認"""
        logger.info("UsbCameraAdapter: セットアップ開始")
        if not self.open():
            logger.error("UsbCameraAdapter: カメラデバイスのオープンに失敗しました")
            self._is_ready = False
            return False
        try:
            status = self.check_device_status()
            if status == "READY":
                self._is_ready = True
                logger.info("UsbCameraAdapter: セットアップ完了(READY)")
                return True
            else:
                logger.error(f"UsbCameraAdapter: デバイス準備失敗({status})")
                return False
        except Exception as e:
            logger.exception(f"UsbCameraAdapter: setup エラー: {e}")
            return False
        pass

    async def execute_step(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """アクション名に応じた処理の実行

        setup/teardownはsyncのまま（境界はexecute_stepだけ）。
        OpenCVのブロッキング呼び出しはasyncio.to_threadで別スレッドに逃がし、
        Orchestratorの他の非同期処理を止めないようにする。
        """
        if not self._is_ready:
            raise RuntimeError("カメラがsetupされてません。先にsetup()を呼んでください。")
        logger.info(f"UsbCameraAdapter: action {action} を実行")
        if action == "capture":
            resolution = params.get("resolution")
            if resolution is not None:
                await asyncio.to_thread(self.camera_controller.set_resolution, resolution)
            frame = await asyncio.to_thread(self.camera_controller.capture)
            return {
                "status": "SUCCESS" if frame is not None else "FAILED",
                "frame": frame
            }
        else:
            raise ValueError(f"未対応のアクションです: {action}")

    def teardown(self) -> None:
        """カメラリソースの解放"""
        logger.info("UsbCameraAdapter: リソース解放開始")
        try:
            if hasattr(self.camera_controller, "release"):
                self.camera_controller.release()
            self._is_ready = False
            logger.info("UsbCameraAdapter: リソース解放完了")
        except Exception as e:
            logger.exception(f"UsbCameraAdapter: teardown エラー: {e}")

    def check_device_status(self) -> str:
        is_on = self.camera_controller.is_led_on(self._roi, self._threshold)
        return "READY" if is_on else "NOT_READY"

    def open(self) -> bool:
        return self.camera_controller.open()

    def release(self) -> None:
        self.camera_controller.release()

    def is_opened(self) -> bool:
        return self.camera_controller.is_opened()

    def capture(self) -> np.ndarray | None:
        return self.camera_controller.capture()

    def save_capture(self, frame) -> None:
        self.camera_controller.save_capture(frame=frame)
    
    def is_led_on(self, roi: tuple[int, int, int, int], threshold) -> bool:
        return self.camera_controller.is_led_on(roi=roi, threshold=threshold)
