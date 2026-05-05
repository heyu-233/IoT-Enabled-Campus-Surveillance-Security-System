#!/usr/bin/env python3
"""
浠?RTMP 娴佹崟鑾峰崟甯у苟淇濆瓨涓哄浘鐗?"""

import cv2
import time
import os

def capture_single_frame(rtmp_url, output_path="captured_frame.jpg"):
    """
    浠?RTMP 娴佹崟鑾峰崟甯?
    Args:
        rtmp_url: RTMP 娴佸湴鍧€
        output_path: 淇濆瓨璺緞
    """
    print("=" * 60)
    print("RTMP 娴佸崟甯ф崟鑾?)
    print("=" * 60)

    print(f"\n[INFO] 娴佸湴鍧€: {rtmp_url}")
    print(f"[INFO] 姝ｅ湪杩炴帴...")

    # 鎵撳紑娴?    cap = cv2.VideoCapture(rtmp_url)

    if not cap.isOpened():
        print("[ERROR] 鏃犳硶鎵撳紑瑙嗛娴侊紒")
        print("\n璇锋鏌ワ細")
        print("  1. 鎺ㄦ祦鏄惁姝ｅ湪杩愯")
        print("  2. 缃戠粶杩炴帴鏄惁姝ｅ父")
        print("  3. 娴佸湴鍧€鏄惁姝ｇ‘")
        return False

    print("[OK] 娴佽繛鎺ユ垚鍔燂紒")

    # 璇诲彇鍑犲抚锛岃娴佺ǔ瀹?    print("\n[INFO] 璇诲彇棰勭儹甯?..")
    for i in range(10):
        ret, frame = cap.read()
        if ret:
            print(f"  绗?{i+1} 甯ц鍙栨垚鍔?)
        time.sleep(0.1)

    # 鎹曡幏涓€甯?    print("\n[INFO] 鎹曡幏鐩爣甯?..")
    ret, frame = cap.read()

    if not ret:
        print("[ERROR] 鎹曡幏甯уけ璐ワ紒")
        cap.release()
        return False

    # 淇濆瓨鍥剧墖
    cv2.imwrite(output_path, frame)
    print(f"[OK] 甯у凡淇濆瓨鍒? {os.path.abspath(output_path)}")
    print(f"[INFO] 鍥剧墖灏哄: {frame.shape}")

    # 鏄剧ず鍥剧墖
    print("\n[INFO] 鏄剧ず鎹曡幏鐨勫抚锛堟寜浠绘剰閿叧闂獥鍙ｏ級")
    cv2.imshow("Captured Frame", frame)
    cv2.waitKey(0)

    # 閲婃斁璧勬簮
    cap.release()
    cv2.destroyAllWindows()

    print("\n[OK] 鎹曡幏瀹屾垚锛?)
    return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="浠?RTMP 娴佹崟鑾峰崟甯?)
    parser.add_argument("--url", type=str,
                       default="rtmp://192.168.1.6/myapp/stream",
                       help="RTMP 娴佸湴鍧€")
    parser.add_argument("--output", type=str,
                       default="captured_frame.jpg",
                       help="杈撳嚭鍥剧墖璺緞")

    args = parser.parse_args()

    capture_single_frame(args.url, args.output)
