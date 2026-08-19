from camera_controller.camera_controller import CameraController


def main():
    """pytest収集時に副作用が走らないよう、手動実行専用にガードした動作確認スクリプト"""
    # インスタンス化
    camera = CameraController()
    # カメラOpen
    camera.open()
    # 1フレーム撮影
    frame = camera.capture()
    # 撮影した画像の保存
    camera.save_capture(frame)
    camera.save_roi_capture(frame, roi=(500, 300, 100, 100))
    # LED判定
    result = camera.is_led_on(roi=(500, 300, 100, 100), threshold=120)
    print(result)
    # カメラrelease
    camera.release()


if __name__ == "__main__":
    main()
