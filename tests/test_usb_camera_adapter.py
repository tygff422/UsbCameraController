import asyncio

from usb_camera_adapter.usb_camera_adapter import UsbCameraAdapter
from test_support.usb_camera_mock_controller import UsbCameraMockController

# UsbCameraAdapterの直接メソッド群（open/capture/release等）は削除済み（01_docs/known_issues.md
# No.10対応）。正式な入口はexecute_step()だけになったため、テストもexecute_step()経由に統一する。
# open/release自体の検証はwith構文（setup/teardown）のライフサイクルテストでカバーする。


def test_adapter_setup_teardown_lifecycle():
    """with構文でsetup（接続）/teardown（解放）が呼ばれることを、Fakeのopen状態で確認する。"""
    camera_mock_controller = UsbCameraMockController()

    with UsbCameraAdapter(camera_controller=camera_mock_controller) as adapter:
        assert camera_mock_controller.is_opened() is True

    assert camera_mock_controller.is_opened() is False


def test_adapter_execute_step_capture():
    camera_mock_controller = UsbCameraMockController()

    with UsbCameraAdapter(camera_controller=camera_mock_controller) as adapter:
        result = asyncio.run(adapter.execute_step(action="capture", params={"resolution": [640, 480]}))

    assert result["status"] == "SUCCESS"
    assert result["frame"].shape == (480, 640, 3)


def test_adapter_execute_step_check_status_ready():
    camera_mock_controller = UsbCameraMockController()
    camera_mock_controller.set_led_status(status=True)

    with UsbCameraAdapter(camera_controller=camera_mock_controller) as adapter:
        result = asyncio.run(adapter.execute_step(action="check_status", params={}))

    assert result["status"] == "READY"


def test_adapter_execute_step_check_status_not_ready():
    camera_mock_controller = UsbCameraMockController()
    camera_mock_controller.set_led_status(status=False)

    with UsbCameraAdapter(camera_controller=camera_mock_controller) as adapter:
        result = asyncio.run(adapter.execute_step(action="check_status", params={}))

    assert result["status"] == "NOT_READY"
