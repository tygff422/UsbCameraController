from camera_adapter.camera_adapter import CameraAdapter
from test_support.camera_mock_controller import CameraMockController


def test_adapter_open_capture_release():
    camera_mock_controller = CameraMockController()
    camera_adapter = CameraAdapter(camera_controller=camera_mock_controller)

    assert camera_adapter.capture() is None

    assert camera_adapter.open() is True
    assert camera_adapter.is_opened() is True

    frame = camera_adapter.capture()
    assert frame is not None
    assert frame.shape == (480, 640, 3)

    camera_adapter.release()
    assert camera_adapter.is_opened() == False

def test_adapter_check_device_status():
    camera_mock_controller = CameraMockController()
    camera_adapter = CameraAdapter(camera_controller=camera_mock_controller)

    assert camera_adapter.check_device_status() == "NOT_READY"

    camera_adapter.open()
    camera_mock_controller.set_led_status(status=True)
    assert camera_adapter.check_device_status() == "READY"

def test_adapter_enter_exit():
    camera_mock_controller = CameraMockController()
    camera_mock_controller.set_led_status(status=True)
    with CameraAdapter(camera_controller=camera_mock_controller) as adapter:
        is_opened = adapter.is_opened()
        assert is_opened is True

        frame = adapter.capture()
        assert frame.shape == (480, 640, 3)

    is_opened = adapter.is_opened()
    assert is_opened is False

