# usb-camera-adapter

USBカメラをOpenCV経由で操作する、`scenario_test`ワークスペース内の独立パッケージ（別GitHubリポジトリ：`https://github.com/tygff422/UsbCameraController`）。

## 実装要件（当初の構想）

- OpenCV使用
- 接続管理（カメラを開く・閉じる）
- 画像取得（1フレームの撮影）
- 状態解析（ROIの明るさを閾値と比較、LED点灯判定）

## 収録パッケージ

```text
src/
  camera_controller/  ← 実際にOpenCVを叩く層（open/capture/release/save_capture/is_led_on等）
  camera_adapter/     ← BaseAdapter（adapter-core）実装。Orchestratorとの橋渡し
  interfaces/         ← CameraControllerInterface（Controllerの契約）
```

### `CameraController`

```python
CameraController(device_id: int = 0, img_dir: str | Path | None = None)
```

- `open()` / `release()` / `is_opened()`：接続管理
- `set_resolution(resolution)` / `capture()`：解像度設定・1フレーム撮影
- `save_capture(frame)` / `save_roi_capture(frame, roi)`：撮影画像をファイル保存。戻り値は保存先`Path`（保存しなかった場合は`None`）
  - 実行ごとにタイムスタンプ付きファイル名で残す（例：`capture_20260822_161224_311.png`）
  - `img_dir`未指定なら自パッケージ内`img/`に保存（後方互換のデフォルト）。呼び出し側が上書き可能
    （`scenario_test`側では`testexecutor/img/`に向けている。詳細は[decisions/14](../../01_docs/decisions/14_testexecutor_folder.md)）
- `is_led_on(roi, threshold)`：指定ROIの平均輝度がしきい値を超えるか判定

### `CameraAdapter`（`BaseAdapter`実装）

```python
CameraAdapter(config: dict | None = None, camera_controller=None)
```

- `setup()`：`camera_controller.open()`のみ（接続確認）。LED確認はここでは行わない
  （以前は行っていたが、呼び出し元と二重に撮影してしまうバグがあったため撤去。
  詳細は[decisions/12](../../01_docs/decisions/12_essential_gaps_found.md)）
- `execute_step(action, params)`：`async def`。対応は`"capture"`／`"check_status"`
  - `"capture"`：`params.resolution`があれば解像度設定。撮影後、`save_capture()`を自動で呼ぶ。戻り値の`saved_path`に保存先が入る
  - `"check_status"`：`check_device_status()`（LED点灯判定）を呼ぶ。戻り値の`status`に`"READY"`/`"NOT_READY"`が入る
    （以前はデモ用`Orchestrator`経由でしか呼べなかった機能。詳細は[decisions/19](../../01_docs/decisions/19_orchestrator_demo_class_removal.md)）
  - OpenCVのブロッキング呼び出しは`asyncio.to_thread`で分離（詳細は[decisions/09](../../01_docs/decisions/09_async_execute_step.md)）
- `teardown()`：`camera_controller.release()`
- `config`で受け取るキー：`device_id`（デフォルト0）、`img_dir`（省略可）
- `open()`/`release()`/`is_opened()`/`capture()`/`save_capture()`/`is_led_on()`等の直接メソッドは持たない。
  正式な入口は`execute_step()`のみ（[known_issues.md No.10](../../01_docs/known_issues.md)対応）

`GenericOrchestrator`から`workflow.yaml`経由で動的ロードされる想定（詳細は[orchestrator/README.md](../../orchestrator/README.md)）。

## テスト

```bash
pytest adapters/usb_camera_adapter/tests -m "not hardware"
```

- `test_camera_adapter.py`：`CameraMockController`（Fake、`tests/test_support/`）を使い、`execute_step()`経由で実機なしで検証
- `test_camera_controller.py`：pytestのテストではなく、`main()`ガード付きの手動実行専用スクリプト
  （実機カメラで`open→capture→save→is_led_on→release`を一通り試す用）

実機カメラでの動作確認は、`scenario_test`側の`testexecutor/run_scenario.py`、または
`integrationtest/`の`@pytest.mark.hardware`が付いたテストを参照。

## 関連ドキュメント

このリポジトリ自体には設計判断の記録を置いていない。`scenario_test`側の`01_docs/decisions/`に、このパッケージに関する決定も含めて記録している（[03](../../01_docs/decisions/03_package_settings_adapter_orchestrator.md)・[04](../../01_docs/decisions/04_urgent_fix_camera_pipeline.md)・[06](../../01_docs/decisions/06_workflow_yaml_usage.md)・[09](../../01_docs/decisions/09_async_execute_step.md)・[12](../../01_docs/decisions/12_essential_gaps_found.md)・[13](../../01_docs/decisions/13_log_and_artifact_storage_gap.md)・[14](../../01_docs/decisions/14_testexecutor_folder.md)）。
