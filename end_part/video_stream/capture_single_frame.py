#!/usr/bin/env python3
"""
Capture a single frame from an RTMP stream and save it to disk.
"""

from __future__ import annotations

import argparse
import os
import time

import cv2


def capture_single_frame(rtmp_url: str, output_path: str = "captured_frame.jpg") -> bool:
    print("=" * 60)
    print("RTMP single-frame capture")
    print("=" * 60)
    print(f"[INFO] Stream URL: {rtmp_url}")
    print("[INFO] Connecting...")

    cap = cv2.VideoCapture(rtmp_url)
    if not cap.isOpened():
        print("[ERROR] Failed to open the RTMP stream.")
        print("Check that the stream is running and the URL is correct.")
        return False

    print("[OK] Stream connected.")
    print("[INFO] Warming up frames...")
    for _ in range(10):
        cap.read()
        time.sleep(0.1)

    ok, frame = cap.read()
    if not ok or frame is None:
        print("[ERROR] Failed to capture a frame.")
        cap.release()
        return False

    cv2.imwrite(output_path, frame)
    print(f"[OK] Saved frame to: {os.path.abspath(output_path)}")
    print(f"[INFO] Frame shape: {frame.shape}")

    cap.release()
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture one frame from an RTMP stream")
    parser.add_argument(
        "--url",
        default="rtmp://127.0.0.1:1935/myapp/stream",
        help="RTMP stream URL",
    )
    parser.add_argument(
        "--output",
        default="captured_frame.jpg",
        help="Output image path",
    )
    args = parser.parse_args()

    return 0 if capture_single_frame(args.url, args.output) else 1


if __name__ == "__main__":
    raise SystemExit(main())
