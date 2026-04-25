#!/usr/bin/env python3
"""
RTMP 视频流测试脚本
用于验证 RTMP 流拉取功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rtmp_stream_capture import RTMPStreamCapture
import cv2
import time

def test_rtmp_connection():
    """测试 RTMP 连接"""
    print("=" * 60)
    print("RTMP 视频流连接测试")
    print("=" * 60)
    
    # 创建捕获器
    capture = RTMPStreamCapture(
        rtmp_url='rtmp://127.0.0.1/myapp/stream',
        detect_fps=5,
        display_fps=30
    )
    
    # 尝试连接
    if capture.connect():
        print("\n[OK] 连接测试成功！")
        print("\n正在获取视频帧...")
        
        # 读取几帧测试
        for i in range(10):
            ret, frame = capture.cap.read()
            if ret:
                print(f"  成功读取第 {i+1} 帧，尺寸: {frame.shape}")
            else:
                print(f"  [ERROR] 第 {i+1} 帧读取失败")
            time.sleep(0.1)
        
        # 释放资源
        capture.cap.release()
        print("\n[OK] 测试完成")
        return True
    else:
        print("\n[ERROR] 连接测试失败")
        return False

def test_with_display():
    """测试带显示的视频流"""
    print("\n" + "=" * 60)
    print("RTMP 视频流显示测试")
    print("=" * 60)
    
    capture = RTMPStreamCapture(
        rtmp_url='rtmp://127.0.0.1/myapp/stream',
        detect_fps=5,
        display_fps=30
    )
    
    if not capture.start():
        print("[ERROR] 启动失败")
        return False
    
    print("\n按 'q' 键退出")
    print("=" * 60)
    
    detect_count = 0
    
    try:
        while True:
            # 获取显示帧
            display_frame = capture.get_frame_for_display()
            if display_frame is not None:
                # 添加文字信息
                stats = capture.get_stats()
                info_text = f"FPS: {stats['fps']:.1f} | Frames: {stats['total_frames']}"
                cv2.putText(display_frame, info_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow('RTMP Stream Test', display_frame)
            
            # 获取检测帧
            detect_frame = capture.get_frame_for_detection()
            if detect_frame is not None:
                detect_count += 1
                print(f"[DETECT] 第 {detect_count} 次检测触发")
            
            # 检查退出键
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\n用户中断")
    
    finally:
        capture.stop()
        cv2.destroyAllWindows()
        print(f"\n[OK] 测试完成，共触发 {detect_count} 次检测")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='RTMP 视频流测试')
    parser.add_argument('--mode', choices=['connect', 'display'], 
                       default='connect',
                       help='测试模式: connect=仅测试连接, display=带显示测试')
    
    args = parser.parse_args()
    
    if args.mode == 'connect':
        test_rtmp_connection()
    else:
        test_with_display()
