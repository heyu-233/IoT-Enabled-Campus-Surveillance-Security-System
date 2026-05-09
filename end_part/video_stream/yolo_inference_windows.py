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
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO
import torch


LOGGER = logging.getLogger("detector-supervisor")


@dataclass
class StreamRuntime:
    device_id: str
    rtmp_url: str
    detect_fps: int
    retry_seconds: float
    dedupe_window_seconds: float
    dedupe_iou_threshold: float
    detect_interval: float
    detect_enabled: threading.Event = field(default_factory=threading.Event)
    state_lock: threading.RLock = field(default_factory=threading.RLock)
    frame_lock: threading.Lock = field(default_factory=threading.Lock)
    frame_ready: threading.Condition = field(init=False)
    capture: cv2.VideoCapture | None = None
    capture_thread: threading.Thread | None = None
    capture_interval: float = 0.0
    latest_frame: Any = None
    latest_frame_seq: int = 0
    last_processed_seq: int = 0
    last_result_at: float = 0.0
    detect_count: int = 0
    recent_detections: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    class_hit_history: dict[str, list[float]] = field(default_factory=dict)
    last_reported_by_class: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.frame_ready = threading.Condition(self.frame_lock)


class DetectorSupervisor:
    def __init__(
        self,
        rtmp_url: str,
        backend_url: str,
        model_path: str,
        secondary_model_path: str | None,
        fight_model_path: str | None,
        primary_allowed_classes: set[str],
        secondary_allowed_classes: set[str],
        fight_allowed_classes: set[str],
        primary_min_confidence: float,
        secondary_min_confidence: float,
        fight_min_confidence: float,
        confirmation_window_seconds: float,
        report_cooldown_seconds: float,
        temporal_confirmations: dict[str, int],
        detect_fps: int,
        device_id: str,
        retry_seconds: float,
        jpeg_quality: int,
        dedupe_window_seconds: float,
        dedupe_iou_threshold: float,
        infer_device: str,
    ) -> None:
        self.rtmp_url = rtmp_url
        self.backend_url = backend_url
        self.model_path = model_path
        self.secondary_model_path = secondary_model_path
        self.fight_model_path = fight_model_path
        self.primary_allowed_classes = primary_allowed_classes
        self.secondary_allowed_classes = secondary_allowed_classes
        self.fight_allowed_classes = fight_allowed_classes
        self.primary_min_confidence = min(max(primary_min_confidence, 0.0), 1.0)
        self.secondary_min_confidence = min(max(secondary_min_confidence, 0.0), 1.0)
        self.fight_min_confidence = min(max(fight_min_confidence, 0.0), 1.0)
        self.confirmation_window_seconds = max(0.1, confirmation_window_seconds)
        self.report_cooldown_seconds = max(0.0, report_cooldown_seconds)
        self.temporal_confirmations = temporal_confirmations
        self.detect_fps = max(1, detect_fps)
        self.device_id = device_id
        self.retry_seconds = max(1.0, retry_seconds)
        self.jpeg_quality = min(max(jpeg_quality, 30), 95)
        self.dedupe_window_seconds = max(0.5, dedupe_window_seconds)
        self.dedupe_iou_threshold = min(max(dedupe_iou_threshold, 0.1), 0.95)
        self.infer_device = self._resolve_infer_device(infer_device)

        self.detect_interval = 1.0 / self.detect_fps
        self.shutdown_event = threading.Event()
        self.detect_enabled = threading.Event()
        self.state_lock = threading.RLock()
        self.frame_lock = threading.Lock()
        self.frame_ready = threading.Condition(self.frame_lock)
        self.streams_lock = threading.RLock()
        self.streams: dict[str, StreamRuntime] = {}
        self._shutdown_started = False

        self.model: YOLO | None = None
        self.secondary_model: YOLO | None = None
        self.fight_model: YOLO | None = None
        self.capture: cv2.VideoCapture | None = None
        self.capture_thread: threading.Thread | None = None
        self.inference_thread: threading.Thread | None = None
        self.http_server: ThreadingHTTPServer | None = None
        self.http_thread: threading.Thread | None = None
        self.latest_frame: Any = None
        self.latest_frame_seq = 0

        self.detect_count = 0
        self.last_result_at = 0.0
        self.recent_detections: dict[str, list[dict[str, Any]]] = {}
        self.class_hit_history: dict[str, list[float]] = {}
        self.last_reported_by_class: dict[str, float] = {}

    def _resolve_infer_device(self, requested_device: str) -> str:
        normalized = (requested_device or "auto").strip().lower()
        if normalized == "auto":
            if torch.cuda.is_available():
                resolved = "0"
                LOGGER.info("CUDA detected, using GPU device %s for YOLO inference", resolved)
                return resolved
            LOGGER.info("CUDA not available, falling back to CPU inference")
            return "cpu"

        if normalized in {"cuda", "cuda:0", "0", "gpu"}:
            if torch.cuda.is_available():
                return "0"
            LOGGER.warning("GPU device %s was requested but CUDA is unavailable, falling back to CPU", requested_device)
            return "cpu"

        return requested_device

    def _get_or_create_stream(self, device_id: str | None = None) -> StreamRuntime:
        normalized_device_id = (device_id or self.device_id or "windows-edge-001").strip()
        with self.streams_lock:
            stream = self.streams.get(normalized_device_id)
            if stream is not None:
                return stream

            stream = StreamRuntime(
                device_id=normalized_device_id,
                rtmp_url=self.rtmp_url,
                detect_fps=self.detect_fps,
                retry_seconds=self.retry_seconds,
                dedupe_window_seconds=self.dedupe_window_seconds,
                dedupe_iou_threshold=self.dedupe_iou_threshold,
                detect_interval=1.0 / self.detect_fps,
            )
            self.streams[normalized_device_id] = stream
            return stream

    def _active_streams(self) -> list[StreamRuntime]:
        with self.streams_lock:
            return [stream for stream in self.streams.values() if stream.detect_enabled.is_set()]

    def _all_streams(self) -> list[StreamRuntime]:
        with self.streams_lock:
            return list(self.streams.values())

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
        LOGGER.info("YOLO inference device is %s", self.infer_device)

        self.secondary_model, self.secondary_model_path = self._load_optional_model(
            self.secondary_model_path,
            "secondary",
        )
        self.fight_model, self.fight_model_path = self._load_optional_model(
            self.fight_model_path,
            "fight",
        )
        LOGGER.info(
            "Model routing: primary classes=%s, secondary classes=%s, fight classes=%s",
            sorted(self.primary_allowed_classes),
            sorted(self.secondary_allowed_classes),
            sorted(self.fight_allowed_classes),
        )
        LOGGER.info(
            "Model confidence floors: primary=%.2f, secondary=%.2f, fight=%.2f",
            self.primary_min_confidence,
            self.secondary_min_confidence,
            self.fight_min_confidence,
        )
        LOGGER.info(
            "Temporal filters: confirmations=%s, window=%.1fs, report cooldown=%.1fs",
            self.temporal_confirmations,
            self.confirmation_window_seconds,
            self.report_cooldown_seconds,
        )

    def _load_optional_model(self, model_path: str | None, model_label: str) -> tuple[YOLO | None, str | None]:
        if not model_path:
            LOGGER.info("%s YOLO model is disabled", model_label.capitalize())
            return None, None

        model_candidate = Path(model_path)
        if not model_candidate.is_absolute():
            model_candidate = Path(__file__).resolve().parent / model_candidate

        resolved_path = str(model_candidate)
        if not model_candidate.exists():
            LOGGER.warning("%s model file not found, disabling it: %s", model_label.capitalize(), resolved_path)
            return None, None

        LOGGER.info("Loading %s YOLO model from %s", model_label, resolved_path)
        return YOLO(resolved_path), resolved_path

    def start_detection(self, payload: dict[str, Any] | None = None) -> None:
        target_device = str((payload or {}).get("device_id", self.device_id)).strip() or self.device_id
        stream = self._get_or_create_stream(target_device)
        if payload:
            self.update_config(payload)

        if stream.detect_enabled.is_set():
            LOGGER.info("Detection already enabled for %s", stream.device_id)
            return

        stream.detect_enabled.set()
        if stream.capture_thread is None or not stream.capture_thread.is_alive():
            stream.capture_thread = threading.Thread(
                target=self._capture_loop,
                args=(stream,),
                name=f"detector-capture-{stream.device_id}",
                daemon=True,
            )
            stream.capture_thread.start()
        LOGGER.info("Detection enabled for %s", stream.device_id)

    def stop_detection(self, payload: dict[str, Any] | None = None) -> None:
        target_device = str((payload or {}).get("device_id", "")).strip()
        if target_device:
            streams = [self._get_or_create_stream(target_device)]
        else:
            streams = self._all_streams()

        if not streams:
            LOGGER.info("Detection already disabled")
            return

        for stream in streams:
            if not stream.detect_enabled.is_set():
                LOGGER.info("Detection already disabled for %s", stream.device_id)
                self._close_capture(stream)
                continue

            stream.detect_enabled.clear()
            stream.last_result_at = 0.0
            self._close_capture(stream)
            self._clear_latest_frame(stream)
            LOGGER.info("Detection disabled for %s", stream.device_id)

    def update_config(self, payload: dict[str, Any]) -> None:
        if not payload:
            return

        target_device = str(payload.get("device_id", self.device_id)).strip() or self.device_id
        stream = self._get_or_create_stream(target_device)

        with stream.state_lock:
            new_rtmp = payload.get("rtmp_url")
            if isinstance(new_rtmp, str) and new_rtmp.strip() and new_rtmp.strip() != stream.rtmp_url:
                stream.rtmp_url = new_rtmp.strip()
                LOGGER.info("Updated video source for %s to %s", stream.device_id, stream.rtmp_url)
                self._close_capture(stream)

            new_fps = payload.get("detect_fps")
            if isinstance(new_fps, (int, float)) and float(new_fps) > 0:
                stream.detect_fps = max(1, int(new_fps))
                stream.detect_interval = 1.0 / stream.detect_fps
                LOGGER.info("Updated detect_fps for %s to %s", stream.device_id, stream.detect_fps)

            new_retry = payload.get("retry_seconds")
            if isinstance(new_retry, (int, float)) and float(new_retry) > 0:
                stream.retry_seconds = max(1.0, float(new_retry))
                LOGGER.info("Updated retry_seconds for %s to %s", stream.device_id, stream.retry_seconds)

            new_dedupe_window = payload.get("dedupe_window_seconds")
            if isinstance(new_dedupe_window, (int, float)) and float(new_dedupe_window) > 0:
                stream.dedupe_window_seconds = max(0.5, float(new_dedupe_window))
                LOGGER.info("Updated dedupe_window_seconds for %s to %s", stream.device_id, stream.dedupe_window_seconds)

            new_dedupe_iou = payload.get("dedupe_iou_threshold")
            if isinstance(new_dedupe_iou, (int, float)) and 0 < float(new_dedupe_iou) < 1:
                stream.dedupe_iou_threshold = min(max(float(new_dedupe_iou), 0.1), 0.95)
                LOGGER.info("Updated dedupe_iou_threshold for %s to %s", stream.device_id, stream.dedupe_iou_threshold)

    def run(self) -> None:
        self.load_model()
        self.start_http_server()

        self.inference_thread = threading.Thread(target=self._inference_loop, name="detector-inference", daemon=True)
        self.inference_thread.start()

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
        for stream in self._all_streams():
            stream.detect_enabled.clear()
            self._close_capture(stream)
            self._clear_latest_frame(stream)
            with stream.frame_ready:
                stream.frame_ready.notify_all()

        for stream in self._all_streams():
            if stream.capture_thread is not None and stream.capture_thread.is_alive():
                stream.capture_thread.join(timeout=5.0)
        if self.inference_thread is not None and self.inference_thread.is_alive():
            self.inference_thread.join(timeout=5.0)

        if self.http_server is not None:
            self.http_server.shutdown()
            self.http_server.server_close()

        if self.http_thread is not None and self.http_thread.is_alive():
            self.http_thread.join(timeout=5.0)

        try:
            cv2.destroyAllWindows()
        except Exception:
            LOGGER.debug("destroyAllWindows failed during shutdown", exc_info=True)

    def _ensure_capture(self, stream: StreamRuntime) -> bool:
        with stream.state_lock:
            if stream.capture is not None and stream.capture.isOpened():
                return True

            LOGGER.info("Opening video source for %s: %s", stream.device_id, stream.rtmp_url)
            stream.capture = self._open_video_capture(stream.rtmp_url)
            if stream.capture is None or not stream.capture.isOpened():
                LOGGER.warning("Failed to open video source for %s, retry in %.1fs", stream.device_id, stream.retry_seconds)
                self._close_capture(stream)
                return False

            stream.capture_interval = self._capture_interval_for_source(stream)
            LOGGER.info("Video source connected for %s", stream.device_id)
            return True

    def _open_video_capture(self, source: str) -> cv2.VideoCapture:
        normalized = source.strip()
        if normalized.isdigit():
            return cv2.VideoCapture(int(normalized))
        return cv2.VideoCapture(normalized)

    def _close_capture(self, stream: StreamRuntime) -> None:
        with stream.state_lock:
            if stream.capture is not None:
                try:
                    stream.capture.release()
                finally:
                    stream.capture = None

    def _store_latest_frame(self, stream: StreamRuntime, frame: Any) -> None:
        with stream.frame_ready:
            stream.latest_frame = frame
            stream.latest_frame_seq += 1
            stream.frame_ready.notify()

    def _clear_latest_frame(self, stream: StreamRuntime) -> None:
        with stream.frame_ready:
            stream.latest_frame = None
            stream.latest_frame_seq += 1
            stream.frame_ready.notify_all()

    def _read_frame(self, stream: StreamRuntime) -> tuple[bool, Any]:
        with stream.state_lock:
            if stream.capture is None:
                return False, None
            return stream.capture.read()

    def _capture_loop(self, stream: StreamRuntime) -> None:
        while not self.shutdown_event.is_set():
            if not stream.detect_enabled.wait(timeout=0.5):
                self._close_capture(stream)
                self._clear_latest_frame(stream)
                continue

            if not self._ensure_capture(stream):
                self._sleep_with_shutdown(stream.retry_seconds)
                continue

            ok, frame = self._read_frame(stream)
            if not ok or frame is None:
                if self._rewind_local_video(stream):
                    continue

                LOGGER.warning("Stream read failed for %s, reconnect in %.1fs", stream.device_id, stream.retry_seconds)
                self._close_capture(stream)
                self._clear_latest_frame(stream)
                self._sleep_with_shutdown(stream.retry_seconds)
                continue

            # Keep only the most recent frame so inference stays close to real time.
            self._store_latest_frame(stream, frame.copy())
            self._pace_local_video(stream)

    def _rewind_local_video(self, stream: StreamRuntime) -> bool:
        with stream.state_lock:
            if stream.capture is None or not self._is_local_video_source(stream.rtmp_url):
                return False

            frame_count = stream.capture.get(cv2.CAP_PROP_FRAME_COUNT)
            if frame_count <= 0:
                return False

            LOGGER.info("Local video source for %s reached the end, rewinding to the first frame", stream.device_id)
            stream.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = stream.capture.read()
            if not ok or frame is None:
                self._close_capture(stream)
                return False

        self._store_latest_frame(stream, frame.copy())
        self._pace_local_video(stream)
        return True

    def _capture_interval_for_source(self, stream: StreamRuntime) -> float:
        if not self._is_local_video_source(stream.rtmp_url):
            return 0.0

        fps = 0.0
        if stream.capture is not None:
            fps = float(stream.capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps <= 0:
            fps = float(stream.detect_fps)
        return 1.0 / max(1.0, min(fps, 30.0))

    def _pace_local_video(self, stream: StreamRuntime) -> None:
        if stream.capture_interval > 0:
            self._sleep_with_shutdown(stream.capture_interval)

    def _is_local_video_source(self, source: str) -> bool:
        normalized = source.strip().lower()
        if normalized.startswith(("rtmp://", "rtsp://", "http://", "https://")):
            return False
        return Path(source).suffix.lower() in {".mp4", ".avi", ".mov", ".mkv", ".m4v", ".webm"}

    def _inference_loop(self) -> None:
        while not self.shutdown_event.is_set():
            active_streams = self._active_streams()
            if not active_streams:
                self._sleep_with_shutdown(0.2)
                continue

            did_work = False
            for stream in active_streams:
                if self.shutdown_event.is_set() or not stream.detect_enabled.is_set():
                    continue

                with stream.frame_ready:
                    if stream.latest_frame is None or stream.latest_frame_seq == stream.last_processed_seq:
                        continue
                    frame = stream.latest_frame.copy()
                    current_seq = stream.latest_frame_seq

                now = time.time()
                if now - stream.last_result_at < stream.detect_interval:
                    continue

                stream.last_result_at = now
                stream.last_processed_seq = current_seq
                did_work = True
                try:
                    self._run_inference(frame, stream)
                except Exception:
                    LOGGER.exception("Inference loop failed for %s, keeping supervisor alive", stream.device_id)
                    self._sleep_with_shutdown(stream.retry_seconds)

            if not did_work:
                self._sleep_with_shutdown(0.05)

    def _run_inference(self, frame: Any, stream: StreamRuntime) -> None:
        if self.model is None:
            raise RuntimeError("model is not loaded")

        primary_results = self.model(frame, verbose=False, device=self.infer_device)
        detections = self._collect_detections(
            primary_results,
            self.model,
            model_source="primary",
            allowed_classes=self.primary_allowed_classes,
            min_confidence=self.primary_min_confidence,
        )
        if self.secondary_model is not None:
            secondary_results = self.secondary_model(frame, verbose=False, device=self.infer_device)
            detections.extend(
                self._collect_detections(
                    secondary_results,
                    self.secondary_model,
                    model_source="fire_smoke",
                    allowed_classes=self.secondary_allowed_classes,
                    min_confidence=self.secondary_min_confidence,
                )
            )
        if self.fight_model is not None:
            fight_results = self.fight_model(frame, verbose=False, device=self.infer_device)
            detections.extend(
                self._collect_detections(
                    fight_results,
                    self.fight_model,
                    model_source="fight",
                    allowed_classes=self.fight_allowed_classes,
                    min_confidence=self.fight_min_confidence,
                )
            )

        now = time.time()
        detections = self._apply_temporal_filters(stream, detections, now)
        detections = self._filter_duplicate_detections(stream, detections, now)
        stream.detect_count += 1

        if not detections or not stream.detect_enabled.is_set():
            return

        annotated_frame = self._draw_detections(frame, detections)
        payload = {
            "device_id": stream.device_id,
            "timestamp": int(time.time()),
            "detections": detections,
            "original_image": self._encode_frame(frame),
            "processed_image": self._encode_frame(annotated_frame),
        }
        self._post_detection(payload)
        LOGGER.info("Posted %s detections for %s (total runs=%s)", len(detections), stream.device_id, stream.detect_count)

    def _apply_temporal_filters(self, stream: StreamRuntime, detections: list[dict[str, Any]], now: float) -> list[dict[str, Any]]:
        if not detections:
            return []

        cutoff = now - self.confirmation_window_seconds
        classes_seen = {str(detection.get("class", "unknown")) for detection in detections}
        for class_name in classes_seen:
            history = [
                timestamp for timestamp in stream.class_hit_history.get(class_name, [])
                if timestamp >= cutoff
            ]
            history.append(now)
            stream.class_hit_history[class_name] = history

        filtered: list[dict[str, Any]] = []
        reported_this_frame: set[str] = set()
        for detection in detections:
            class_name = str(detection.get("class", "unknown"))
            required_hits = max(1, self.temporal_confirmations.get(class_name, 1))
            hit_count = len(stream.class_hit_history.get(class_name, []))
            if hit_count < required_hits:
                LOGGER.debug(
                    "Suppressing %s until temporal confirmation reaches %s/%s",
                    class_name,
                    hit_count,
                    required_hits,
                )
                continue

            last_reported_at = stream.last_reported_by_class.get(class_name, 0.0)
            if now - last_reported_at < self.report_cooldown_seconds:
                LOGGER.debug("Suppressing %s during %.1fs report cooldown", class_name, self.report_cooldown_seconds)
                continue

            if class_name in reported_this_frame:
                continue

            filtered.append(detection)
            reported_this_frame.add(class_name)
            stream.last_reported_by_class[class_name] = now

        stale_classes = [
            class_name for class_name, timestamps in stream.class_hit_history.items()
            if not timestamps or all(timestamp < cutoff for timestamp in timestamps)
        ]
        for class_name in stale_classes:
            stream.class_hit_history.pop(class_name, None)

        return filtered

    def _filter_duplicate_detections(self, stream: StreamRuntime, detections: list[dict[str, Any]], now: float) -> list[dict[str, Any]]:
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
                item for item in stream.recent_detections.get(class_name, [])
                if float(item.get("timestamp", 0.0)) >= cutoff
            ]
            stream.recent_detections[class_name] = recent_items

            is_duplicate = any(
                self._is_same_detection(bbox, item.get("bbox", {}))
                for item in recent_items
            )
            if is_duplicate:
                continue

            recent_items.append({"timestamp": now, "bbox": bbox})
            stream.recent_detections[class_name] = recent_items
            filtered.append(detection)

        stale_classes = [
            class_name for class_name, items in stream.recent_detections.items()
            if not items or all(float(item.get("timestamp", 0.0)) < cutoff for item in items)
        ]
        for class_name in stale_classes:
            stream.recent_detections.pop(class_name, None)

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

    def _collect_detections(
        self,
        results: Any,
        model: YOLO,
        model_source: str,
        allowed_classes: set[str],
        min_confidence: float,
    ) -> list[dict[str, Any]]:
        detections: list[dict[str, Any]] = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            for box in boxes:
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])
                if confidence < min_confidence:
                    continue
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                class_name = self._normalize_class_name(self._resolve_class_name(model, cls_id))
                if allowed_classes and class_name not in allowed_classes:
                    continue

                detections.append(
                    {
                        "class": class_name,
                        "class_id": cls_id,
                        "confidence": round(confidence, 4),
                        "model_source": model_source,
                        "bbox": {
                            "x1": round(float(x1), 2),
                            "y1": round(float(y1), 2),
                            "x2": round(float(x2), 2),
                            "y2": round(float(y2), 2),
                        },
                    }
                )
        return detections

    def _resolve_class_name(self, model: YOLO, cls_id: int) -> str:
        names = model.names
        if isinstance(names, dict):
            return str(names.get(cls_id, f"class_{cls_id}"))
        if isinstance(names, list) and 0 <= cls_id < len(names):
            return str(names[cls_id])
        return f"class_{cls_id}"

    def _normalize_class_name(self, class_name: str) -> str:
        normalized = class_name.strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "fire": "fire",
            "flame": "fire",
            "smoke": "smoke",
            "knife": "knife",
            "fight": "fight",
            "violence": "fight",
            "violent": "fight",
            "violence_fight": "fight",
            "fight_violence": "fight",
            "physical_altercations": "fight",
            "punching": "fight",
            "kicking": "fight",
        }
        return aliases.get(normalized, normalized)

    def _draw_detections(self, frame: Any, detections: list[dict[str, Any]]) -> Any:
        annotated = frame.copy()
        colors = {
            "fire": (0, 80, 255),
            "smoke": (160, 160, 160),
            "knife": (40, 40, 255),
            "fight": (255, 120, 0),
        }

        for detection in detections:
            bbox = detection.get("bbox")
            if not isinstance(bbox, dict):
                continue
            try:
                x1 = int(float(bbox["x1"]))
                y1 = int(float(bbox["y1"]))
                x2 = int(float(bbox["x2"]))
                y2 = int(float(bbox["y2"]))
            except (KeyError, TypeError, ValueError):
                continue

            class_name = str(detection.get("class", "unknown"))
            confidence = float(detection.get("confidence", 0.0))
            model_source = str(detection.get("model_source", "model"))
            color = colors.get(class_name, (80, 220, 120))
            label = f"{class_name} {confidence:.2f} [{model_source}]"

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label_y = max(16, y1 - 8)
            cv2.putText(
                annotated,
                label,
                (x1, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )

        return annotated

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
            time.sleep(min(0.2, max(0.0, deadline - time.time())))

    def status_payload(self) -> dict[str, Any]:
        streams = self._all_streams()
        selected_stream = next((stream for stream in streams if stream.detect_enabled.is_set()), None)
        if selected_stream is None:
            selected_stream = streams[0] if streams else self._get_or_create_stream(self.device_id)
        return {
            "device_id": selected_stream.device_id,
            "running": any(stream.detect_enabled.is_set() for stream in streams),
            "rtmp_url": selected_stream.rtmp_url,
            "detect_fps": selected_stream.detect_fps,
            "infer_device": self.infer_device,
            "model_path": self.model_path,
            "secondary_model_path": self.secondary_model_path,
            "fight_model_path": self.fight_model_path,
            "primary_allowed_classes": sorted(self.primary_allowed_classes),
            "secondary_allowed_classes": sorted(self.secondary_allowed_classes),
            "fight_allowed_classes": sorted(self.fight_allowed_classes),
            "primary_min_confidence": self.primary_min_confidence,
            "secondary_min_confidence": self.secondary_min_confidence,
            "fight_min_confidence": self.fight_min_confidence,
            "confirmation_window_seconds": self.confirmation_window_seconds,
            "report_cooldown_seconds": self.report_cooldown_seconds,
            "temporal_confirmations": self.temporal_confirmations,
            "retry_seconds": selected_stream.retry_seconds,
            "dedupe_window_seconds": selected_stream.dedupe_window_seconds,
            "dedupe_iou_threshold": selected_stream.dedupe_iou_threshold,
            "detect_count": sum(stream.detect_count for stream in streams),
            "streams": {
                stream.device_id: {
                    "device_id": stream.device_id,
                    "running": stream.detect_enabled.is_set(),
                    "rtmp_url": stream.rtmp_url,
                    "detect_fps": stream.detect_fps,
                    "detect_count": stream.detect_count,
                    "latest_frame_seq": stream.latest_frame_seq,
                }
                for stream in streams
            },
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
                    supervisor.stop_detection(payload)
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
    parser.add_argument("--secondary-model", default=os.getenv("DETECTOR_SECONDARY_MODEL_PATH", "fire_smoke_best.pt"))
    parser.add_argument("--fight-model", default=os.getenv("DETECTOR_FIGHT_MODEL_PATH", "fight_siwon_yolo_best.pt"))
    parser.add_argument("--primary-classes", default=os.getenv("DETECTOR_PRIMARY_CLASSES", "knife"))
    parser.add_argument("--secondary-classes", default=os.getenv("DETECTOR_SECONDARY_CLASSES", "fire,smoke"))
    parser.add_argument("--fight-classes", default=os.getenv("DETECTOR_FIGHT_CLASSES", "fight"))
    parser.add_argument("--primary-min-confidence", type=float, default=float(os.getenv("DETECTOR_PRIMARY_MIN_CONFIDENCE", "0.35")))
    parser.add_argument("--secondary-min-confidence", type=float, default=float(os.getenv("DETECTOR_SECONDARY_MIN_CONFIDENCE", "0.55")))
    parser.add_argument("--fight-min-confidence", type=float, default=float(os.getenv("DETECTOR_FIGHT_MIN_CONFIDENCE", "0.45")))
    parser.add_argument("--confirmation-window-seconds", type=float, default=float(os.getenv("DETECTOR_CONFIRMATION_WINDOW_SECONDS", "3.0")))
    parser.add_argument("--report-cooldown-seconds", type=float, default=float(os.getenv("DETECTOR_REPORT_COOLDOWN_SECONDS", "12")))
    parser.add_argument("--temporal-confirmations", default=os.getenv("DETECTOR_TEMPORAL_CONFIRMATIONS", "fire:2,smoke:2,fight:1,knife:1"))
    parser.add_argument("--fps", type=int, default=int(os.getenv("DETECTOR_FPS", "5")))
    parser.add_argument("--device", default=os.getenv("DETECTOR_DEVICE_ID", "windows-edge-001"))
    parser.add_argument("--infer-device", default=os.getenv("DETECTOR_INFER_DEVICE", "auto"))
    parser.add_argument("--retry-seconds", type=float, default=float(os.getenv("DETECTOR_RETRY_SECONDS", "3")))
    parser.add_argument("--jpeg-quality", type=int, default=int(os.getenv("DETECTOR_JPEG_QUALITY", "70")))
    parser.add_argument("--dedupe-window-seconds", type=float, default=float(os.getenv("DETECTOR_DEDUPE_WINDOW_SECONDS", "8")))
    parser.add_argument("--dedupe-iou-threshold", type=float, default=float(os.getenv("DETECTOR_DEDUPE_IOU_THRESHOLD", "0.45")))
    return parser


def parse_class_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {
        item.strip().lower().replace(" ", "_").replace("-", "_")
        for item in value.split(",")
        if item.strip()
    }


def parse_temporal_confirmations(value: str | None) -> dict[str, int]:
    confirmations: dict[str, int] = {}
    if not value:
        return confirmations

    for item in value.split(","):
        if ":" not in item:
            continue
        class_name, count = item.split(":", 1)
        normalized_class = class_name.strip().lower().replace(" ", "_").replace("-", "_")
        try:
            confirmations[normalized_class] = max(1, int(count.strip()))
        except ValueError:
            LOGGER.warning("Ignoring invalid temporal confirmation item: %s", item)
    return confirmations


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
        secondary_model_path=args.secondary_model.strip() or None,
        fight_model_path=args.fight_model.strip() or None,
        primary_allowed_classes=parse_class_set(args.primary_classes),
        secondary_allowed_classes=parse_class_set(args.secondary_classes),
        fight_allowed_classes=parse_class_set(args.fight_classes),
        primary_min_confidence=args.primary_min_confidence,
        secondary_min_confidence=args.secondary_min_confidence,
        fight_min_confidence=args.fight_min_confidence,
        confirmation_window_seconds=args.confirmation_window_seconds,
        report_cooldown_seconds=args.report_cooldown_seconds,
        temporal_confirmations=parse_temporal_confirmations(args.temporal_confirmations),
        detect_fps=args.fps,
        device_id=args.device,
        infer_device=args.infer_device,
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
