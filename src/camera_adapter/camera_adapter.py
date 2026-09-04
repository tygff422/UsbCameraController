import asyncio
from typing import Any, Dict

from loguru import logger
from camera_controller.camera_controller import CameraController
from adapter_core.baseadapter import BaseAdapter


class CameraAdapter(BaseAdapter):
    def __init__(self, config: Dict[str, Any] | None = None, camera_controller=None):
        if camera_controller is not None:
            self.camera_controller = camera_controller
        else:
            device_id = (config or {}).get("device_id", 0)
            img_dir = (config or {}).get("img_dir")
            self.camera_controller = CameraController(device_id=device_id, img_dir=img_dir)
        self._roi = (100, 150, 50, 50)
        self._threshold = 70
    
    def setup(self) -> bool:
        """カメラの初期化（接続）のみを行う。

        LEDの点灯確認（check_device_status）はここでは呼ばない。以前はここでも
        呼んでいたため、Orchestrator.execute()内の呼び出しと合わせて1回のexecute()で
        2回撮影してしまっていた（01_docs/decisions/12_essential_gaps_found.md参照）。
        LED確認が必要な呼び出し元は、setup後に自分でcheck_device_status()を呼ぶこと。
        """
        logger.info("UsbCameraAdapter: セットアップ開始")
        if not self.camera_controller.open():
            logger.error("UsbCameraAdapter: カメラデバイスのオープンに失敗しました")
            self._is_ready = False
            return False
        self._is_ready = True
        logger.info("UsbCameraAdapter: セットアップ完了(カメラオープン成功)")
        return True

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

            saved_path = None
            if frame is not None:
                saved_path = await asyncio.to_thread(self.camera_controller.save_capture, frame)

            return {
                "status": "SUCCESS" if frame is not None else "FAILED",
                "frame": frame,
                "saved_path": str(saved_path) if saved_path is not None else None,
            }
        elif action == "check_status":
            # LEDのROI画像判定によるデバイス準備確認（01_docs/decisions/19参照）。
            # 以前はデモ用Orchestrator経由でしか呼べなかった機能を、GenericOrchestrator
            # からも使えるように、正規のactionとしてここに配線する。
            led_status = await asyncio.to_thread(self.check_device_status)
            return {"status": led_status}
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
        """LEDのROI画像判定によるデバイス準備確認。execute_step("check_status")から使う内部実装。"""
        is_on = self.camera_controller.is_led_on(self._roi, self._threshold)
        return "READY" if is_on else "NOT_READY"
