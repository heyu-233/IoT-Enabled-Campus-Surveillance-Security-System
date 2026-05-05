#!/usr/bin/env python3
"""
Persistent detector supervisor for the Windows edge node.

The process stays alive after startup, accepts HTTP control commands,
and forwards detection results to the Spring Boot backend via HTTP POST.
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import signal
import threading
import time
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO


LOGGER = logging.getLogger("detector-supervisor")


class DetectorSupervisor:
    def __init__(
        self,
        rtmp_url: str,
        backend_url: str,
        model_path: str,
        detect_fps: int,
        device_id: str,
        retry_seconds: float,
        jpeg_quality: int,
        dedupe_window_seconds: float,
        dedupe_iou_threshold: float,
    ) -> None:
        self.rtmp_url = rtmp_url
        self.backend_url = backend_url
        self.model_path = model_path
        self.detect_fps = max(1, detect_fps)
        self.device_id = device_id
        self.retry_seconds = max(1.0, retry_seconds)
        self.jpeg_quality = min(max(jpeg_quality, 30), 95)
        self.dedupe_window_seconds = max(0.5, dedupe_window_seconds)
        self.dedupe_iou_threshold = min(max(dedupe_iou_threshold, 0.1), 0.95)

        self.detect_interval = 1.0 / self.detect_fps
        self.shutdown_event = threading.Event()
        self.detect_enabled = threading.Event()
        self.state_lock = threading.Lock()
        self._shutdown_started = False

        self.model: YOLO | None = None
        self.capture: cv2.VideoCapture | None = None
        self.worker_thread: threading.Thread | None = None
        self.http_server: ThreadingHTTPServer | None = None
        self.http_thread: threading.Thread | None = None

        self.detect_count = 0
        self.last_result_at = 0.0
        self.recent_detections: dict[str, list[dict[str, Any]]] = {}

    def load_model(self) -> None:
        model_candidate = Path(self.model_path)
        if not model_candidate.is_absolute():
            model_candidate = Path(__file__).resolve().parent / model_candidate

        resolved_path = str(model_candidate)
        if not model_candidate.exists():
            raise FileNotFoundError(f"model file not found: {resolved_path}")

        LOGGER.info("Loading YOLO model from %s", resolved_path)
        self.model = YOLO(resolved_path)
        self.model_path = resolved_path

    def start_detection(self, payload: dict[str, Any] | None = None) -> None:
        if payload:
            target_device = str(payload.get("device_id", "")).strip()
            if target_device and target_device != self.device_id:
                LOGGER.info("Switching active device_id from %s to %s", self.device_id, target_device)
                self.device_id = target_device
            self.update_config(payload)

        if self.detect_enabled.is_set():
            LOGGER.info("Detection already enabled")
            return

        self.detect_enabled.set()
        LOGGER.info("Detection enabled")

    def stop_detection(self) -> None:
        if not self.detect_enabled.is_set():
            LOGGER.info("Detection already disabled")
            self._close_capture()
            return

        self.detect_enabled.clear()
        self.last_result_at = 0.0
        self._close_capture()
        LOGGER.info("Detection disabled")

    def update_config(self, payload: dict[str, Any]) -> None:
        if not payload:
            return

        with self.state_lock:
            new_rtmp = payload.get("rtmp_url")
            if isinstance(new_rtmp, str) and new_rtmp.strip() and new_rtmp.strip() != self.rtmp_url:
                self.rtmp_url = new_rtmp.strip()
                LOGGER.info("Updated RTMP URL to %s", self.rtmp_url)
                self._close_capture()

            new_fps = payload.get("detect_fps")
            if isinstance(new_fps, (int, float)) and float(new_fps) > 0:
                self.detect_fps = max(1, int(new_fps))
                self.detect_interval = 1.0 / self.detect_fps
                LOGGER.info("Updated detect_fps to %s", self.detect_fps)

            new_retry = payload.get("retry_seconds")
            if isinstance(new_retry, (int, float)) and float(new_retry) > 0:
                self.retry_seconds = max(1.0, float(new_retry))
                LOGGER.info("Updated retry_seconds to %s", self.retry_seconds)

            new_dedupe_window = payload.get("dedupe_window_seconds")
            if isinstance(new_dedupe_window, (int, float)) and float(new_dedupe_window) > 0:
                self.dedupe_window_seconds = max(0.5, float(new_dedupe_window))
                LOGGER.info("Updated dedupe_window_seconds to %s", self.dedupe_window_seconds)

            new_dedupe_iou = payload.get("dedupe_iou_threshold")
            if isinstance(new_dedupe_iou, (int, float)) and 0 < float(new_dedupe_iou) < 1:
                self.dedupe_iou_threshold = min(max(float(new_dedupe_iou), 0.1), 0.95)
                LOGGER.info("Updated dedupe_iou_threshold to %s", self.dedupe_iou_threshold)

    def run(self) -> None:
        self.load_model()
        self.start_http_server()

        self.worker_thread = threading.Thread(target=self._detection_loop, name="detector-worker", daemon=True)
        self.worker_thread.start()

        LOGGER.info("Detector supervisor is running and waiting for localhost HTTP control commands")
        try:
            while not self.shutdown_event.is_set():
                time.sleep(1.0)
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        if self._shutdown_started:
            return

        self._shutdown_started = True
        LOGGER.info("Shutting down detector supervisor")
        self.shutdown_event.set()
        self.detect_enabled.clear()
        self._close_capture()

        if self.worker_thread is not None and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)

        if self.http_server is not None:
            self.http_server.shutdown()
            self.http_server.server_close()

        if self.http_thread is not None and self.http_thread.is_alive():
            self.http_thread.join(timeout=5.0)

        try:
            cv2.destroyAllWindows()
        except Exception:
            LOGGER.debug("destroyAllWindows failed during shutdown", exc_info=True)

    def _ensure_capture(self) -> bool:
        with self.state_lock:
            if self.capture is not None and self.capture.isOpened():
                return True

            LOGGER.info("Opening RTMP stream %s", self.rtmp_url)
            self.capture = cv2.VideoCapture(self.rtmp_url)
            if self.capture is None or not self.capture.isOpened():
                LOGGER.warning("Failed to open RTMP stream, retry in %.1fs", self.retry_seconds)
                self._close_capture()
                return False

            LOGGER.info("RTMP stream connected")
            return True

    def _close_capture(self) -> None:
        with self.state_lock:
            if self.capture is not None:
                try:
                    self.capture.release()
                finally:
                    self.capture = None

    def _read_frame(self) -> tuple[bool, Any]:
        with self.state_lock:
            if self.capture is None:
                return False, None
            return self.capture.read()

    def _detection_loop(self) -> None:
        while not self.shutdown_event.is_set():
            if not self.detect_enabled.wait(timeout=0.5):
                continue

            if not self._ensure_capture():
                self._sleep_with_shutdown(self.retry_seconds)
                continue

            ok, frame = self._read_frame()
            if not ok or frame is None:
                LOGGER.warning("Stream read failed, reconnect in %.1fs", self.retry_seconds)
                self._close_capture()
                self._sleep_with_shutdown(self.retry_seconds)
                continue

            now = time.time()
            if now - self.last_result_at < self.detect_interval:
                continue

            self.last_result_at = now
            try:
                self._run_inference(frame)
            except Exception:
                LOGGER.exception("Inference loop failed, keeping supervisor alive")
                self._sleep_with_shutdown(self.retry_seconds)

    def _run_inference(self, frame: Any) -> None:
        if self.model is None:
            raise RuntimeError("model is not loaded")

        results = self.model(frame, verbose=False)
        detections = self._collect_detections(results)
        detections = self._filter_duplicate_detections(detections, time.time())
        self.detect_count += 1

        if not detections or not self.detect_enabled.is_set():
            return

        annotated_frame = results[0].plot()
        payload = {
            "device_id": self.device_id,
            "timestamp": int(time.time()),
            "detections": detections,
            "original_image": self._encode_frame(frame),
            "processed_image": self._encode_frame(annotated_frame),
        }
        self._post_detection(payload)
        LOGGER.info("Posted %s detections (total runs=%s)", len(detections), self.detect_count)

    def _filter_duplicate_detections(self, detections: list[dict[str, Any]], now: float) -> list[dict[str, Any]]:
        if not detections:
            return []

        filtered: list[dict[str, Any]] = []
        cutoff = now - self.dedupe_window_seconds

        for detection in detections:
            class_name = str(detection.get("class", "unknown"))
            bbox = detection.get("bbox")
            if not isinstance(bbox, dict):
                filtered.append(detection)
                continue

            recent_items = [
                item for item in self.recent_detections.get(class_name, [])
                if float(item.get("timestamp", 0.0)) >= cutoff
            ]
            self.recent_detections[class_name] = recent_items

            is_duplicate = any(
                self._is_same_detection(bbox, item.get("bbox", {}))
                for item in recent_items
            )
            if is_duplicate:
                continue

            recent_items.append({"timestamp": now, "bbox": bbox})
            self.recent_detections[class_name] = recent_items
            filtered.append(detection)

        stale_classes = [
            class_name for class_name, items in self.recent_detections.items()
            if not items or all(float(item.get("timestamp", 0.0)) < cutoff for item in items)
        ]
        for class_name in stale_classes:
            self.recent_detections.pop(class_name, None)

        return filtered

    def _is_same_detection(self, left: dict[str, Any], right: dict[str, Any]) -> bool:
        iou = self._bbox_iou(left, right)
        if iou >= self.dedupe_iou_threshold:
            return True

        center_distance_ratio = self._bbox_center_distance_ratio(left, right)
        if center_distance_ratio <= 0.35:
            return True

        return False

    def _bbox_iou(self, left: dict[str, Any], right: dict[str, Any]) -> float:
        try:
            left_x1 = float(left["x1"])
            left_y1 = float(left["y1"])
            left_x2 = float(left["x2"])
            left_y2 = float(left["y2"])
            right_x1 = float(right["x1"])
            right_y1 = float(right["y1"])
            right_x2 = float(right["x2"])
            right_y2 = float(right["y2"])
        except (KeyError, TypeError, ValueError):
            return 0.0

        inter_x1 = max(left_x1, right_x1)
        inter_y1 = max(left_y1, right_y1)
        inter_x2 = min(left_x2, right_x2)
        inter_y2 = min(left_y2, right_y2)

        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h
        if inter_area <= 0:
            return 0.0

        left_area = max(0.0, left_x2 - left_x1) * max(0.0, left_y2 - left_y1)
        right_area = max(0.0, right_x2 - right_x1) * max(0.0, right_y2 - right_y1)
        union_area = left_area + right_area - inter_area
        if union_area <= 0:
            return 0.0
        return inter_area / union_area

    def _bbox_center_distance_ratio(self, left: dict[str, Any], right: dict[str, Any]) -> float:
        try:
            left_x1 = float(left["x1"])
            left_y1 = float(left["y1"])
            left_x2 = float(left["x2"])
            left_y2 = float(left["y2"])
            right_x1 = float(right["x1"])
            right_y1 = float(right["y1"])
            right_x2 = float(right["x2"])
            right_y2 = float(right["y2"])
        except (KeyError, TypeError, ValueError):
            return 1.0

        left_center_x = (left_x1 + left_x2) / 2.0
        left_center_y = (left_y1 + left_y2) / 2.0
        right_center_x = (right_x1 + right_x2) / 2.0
        right_center_y = (right_y1 + right_y2) / 2.0

        center_distance = ((left_center_x - right_center_x) ** 2 + (left_center_y - right_center_y) ** 2) ** 0.5
        left_diag = ((left_x2 - left_x1) ** 2 + (left_y2 - left_y1) ** 2) ** 0.5
        right_diag = ((right_x2 - right_x1) ** 2 + (right_y2 - right_y1) ** 2) ** 0.5
        reference = max(left_diag, right_diag, 1.0)
        return center_distance / reference

    def _collect_detections(self, results: Any) -> list[dict[str, Any]]:
        if self.model is None:
            return []

        detections: list[dict[str, Any]] = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            for box in boxes:
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                names = self.model.names
                if isinstance(names, dict):
                    class_name = names.get(cls_id, f"class_{cls_id}")
                elif isinstance(names, list) and 0 <= cls_id < len(names):
                    class_name = names[cls_id]
                else:
                    class_name = f"class_{cls_id}"
                detections.append(
                    {
                        "class": class_name,
                        "class_id": cls_id,
                        "confidence": round(confidence, 4),
                        "bbox": {
                            "x1": round(float(x1), 2),
                            "y1": round(float(y1), 2),
                            "x2": round(float(x2), 2),
                            "y2": round(float(y2), 2),
                        },
                    }
                )
        return detections

    def _encode_frame(self, frame: Any) -> str | None:
        ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
        if not ok:
            return None
        return base64.b64encode(buffer).decode("utf-8")

    def _post_detection(self, payload: dict[str, Any]) -> None:
        message = {key: value for key, value in payload.items() if value is not None}
        data = json.dumps(message, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.backend_url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            LOGGER.warning("Failed to post detection to backend", exc_info=True)

    def _sleep_with_shutdown(self, seconds: float) -> None:
        deadline = time.time() + seconds
        while time.time() < deadline and not self.shutdown_event.is_set():
            time.sleep(0.2)

    def status_payload(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "running": self.detect_enabled.is_set(),
            "rtmp_url": self.rtmp_url,
            "detect_fps": self.detect_fps,
            "retry_seconds": self.retry_seconds,
            "dedupe_window_seconds": self.dedupe_window_seconds,
            "dedupe_iou_threshold": self.dedupe_iou_threshold,
            "detect_count": self.detect_count,
        }

    def start_http_server(self) -> None:
        supervisor = self

        class ControlHandler(BaseHTTPRequestHandler):
            def _read_json(self) -> dict[str, Any]:
                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length <= 0:
                    return {}
                raw = self.rfile.read(content_length)
                if not raw:
                    return {}
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                    return parsed if isinstance(parsed, dict) else {}
                except json.JSONDecodeError:
                    return {}

            def _write_json(self, status_code: int, payload: dict[str, Any]) -> None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/status":
                    self._write_json(HTTPStatus.OK, supervisor.status_payload())
                else:
                    self._write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

            def do_POST(self) -> None:  # noqa: N802
                payload = self._read_json()
                if self.path == "/start":
                    supervisor.start_detection(payload)
                    self._write_json(HTTPStatus.OK, supervisor.status_payload())
                elif self.path == "/stop":
                    supervisor.stop_detection()
                    self._write_json(HTTPStatus.OK, supervisor.status_payload())
                elif self.path == "/config":
                    supervisor.update_config(payload)
                    self._write_json(HTTPStatus.OK, supervisor.status_payload())
                else:
                    self._write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

            def log_message(self, format: str, *args: Any) -> None:
                LOGGER.debug("http-control " + format, *args)

        self.http_server = ThreadingHTTPServer(("127.0.0.1", 19090), ControlHandler)
        self.http_thread = threading.Thread(
            target=self.http_server.serve_forever,
            name="detector-http-control",
            daemon=True,
        )
        self.http_thread.start()
        LOGGER.info("Detector HTTP control is listening on http://127.0.0.1:19090")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Persistent YOLO detector supervisor")
    parser.add_argument("--rtmp", default=os.getenv("DETECTOR_RTMP_URL", "rtmp://127.0.0.1/myapp/stream"))
    parser.add_argument("--backend-url", default=os.getenv("DETECTOR_BACKEND_URL", "http://127.0.0.1:8081/api/detections"))
    parser.add_argument("--model", default=os.getenv("DETECTOR_MODEL_PATH", "best.pt"))
    parser.add_argument("--fps", type=int, default=int(os.getenv("DETECTOR_FPS", "5")))
    parser.add_argument("--device", default=os.getenv("DETECTOR_DEVICE_ID", "windows-edge-001"))
    parser.add_argument("--retry-seconds", type=float, default=float(os.getenv("DETECTOR_RETRY_SECONDS", "3")))
    parser.add_argument("--jpeg-quality", type=int, default=int(os.getenv("DETECTOR_JPEG_QUALITY", "70")))
    parser.add_argument("--dedupe-window-seconds", type=float, default=float(os.getenv("DETECTOR_DEDUPE_WINDOW_SECONDS", "8")))
    parser.add_argument("--dedupe-iou-threshold", type=float, default=float(os.getenv("DETECTOR_DEDUPE_IOU_THRESHOLD", "0.45")))
    return parser


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def main() -> int:
    configure_logging()
    args = build_arg_parser().parse_args()

    supervisor = DetectorSupervisor(
        rtmp_url=args.rtmp,
        backend_url=args.backend_url,
        model_path=args.model,
        detect_fps=args.fps,
        device_id=args.device,
        retry_seconds=args.retry_seconds,
        jpeg_quality=args.jpeg_quality,
        dedupe_window_seconds=args.dedupe_window_seconds,
        dedupe_iou_threshold=args.dedupe_iou_threshold,
    )

    def handle_signal(_signum: int, _frame: Any) -> None:
        supervisor.shutdown_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_signal)

    try:
        supervisor.run()
        return 0
    except Exception:
        LOGGER.exception("Detector supervisor crashed during startup")
        return 1
    finally:
        supervisor.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
