"""CameraControllerの実機不要な純粋ロジック部分を検証する単体テスト。

open/capture/release等、実際にOpenCVでカメラデバイスを触る部分は実機が必要なため
test_camera_controller.py（手動実行スクリプト）で確認する。ここでは、ファイルパス
生成・画像保存・素朴な条件分岐等、実機カメラに依存しないロジックだけを対象にする
（01_docs/known_issues.md No.2対応）。
"""

import numpy as np

from camera_controller.camera_controller import CameraController


def test_make_img_path_uses_custom_img_dir(tmp_path):
    controller = CameraController(img_dir=tmp_path)

    img_path = controller._make_img_path(img_name="capture")

    assert img_path.parent == tmp_path
    assert img_path.name.startswith("capture_")
    assert img_path.suffix == ".png"


def test_make_img_path_creates_directory_if_missing(tmp_path):
    img_dir = tmp_path / "not_yet_created"
    controller = CameraController(img_dir=img_dir)

    controller._make_img_path(img_name="capture")

    assert img_dir.exists()


def test_save_capture_writes_file(tmp_path):
    controller = CameraController(img_dir=tmp_path)
    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    saved_path = controller.save_capture(frame)

    assert saved_path is not None
    assert saved_path.exists()


def test_save_capture_returns_none_when_frame_is_none(tmp_path):
    controller = CameraController(img_dir=tmp_path)

    assert controller.save_capture(None) is None


def test_save_roi_capture_writes_cropped_file(tmp_path):
    controller = CameraController(img_dir=tmp_path)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    saved_path = controller.save_roi_capture(frame, roi=(10, 10, 20, 20))

    assert saved_path is not None
    assert saved_path.exists()


def test_save_roi_capture_returns_none_when_frame_is_none(tmp_path):
    controller = CameraController(img_dir=tmp_path)

    assert controller.save_roi_capture(None, roi=(10, 10, 20, 20)) is None


def test_is_led_on_returns_false_when_camera_not_opened():
    # open()を呼んでいないため self._cap は None -> capture()がNoneを返す
    # -> is_led_on()は実機を一切触らずFalseを返すはず
    controller = CameraController()

    assert controller.is_led_on(roi=(0, 0, 10, 10), threshold=100) is False
