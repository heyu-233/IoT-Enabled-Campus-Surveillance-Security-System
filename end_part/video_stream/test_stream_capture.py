#!/usr/bin/env python3
"""
测试视频流捕获
"""

import cv2
import time

def test_rtmp_stream(rtmp_url):
    """测试 RTMP 流"""
    print("=" * 60)
    print("RTMP 流拉取测试")
    print("=" * 60)
    
    print(f"\n尝试连接: {rtmp_url}")
    
    cap = cv2.VideoCapture(rtmp_url)
    
    if not cap.isOpened():
        print("[ERROR] 无法打开视频流！")
        print("\n可能的原因：")
        print("  1. 流地址不正确")
        print("  2. 推流服务器未启动")
        print("  3. OpenCV 不支持该协议")
        print("\n尝试使用其他协议（如 RTMP）")
        return False
    
    print("[OK] 视频流连接成功！")
    print("\n按 'q' 键退出窗口")
    print("=" * 60)
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("\n[WARN] 读取帧失败，尝试重新连接...")
                time.sleep(1)
                cap.release()
                cap = cv2.VideoCapture(rtmp_url)
                continue
            
            frame_count += 1
            
            # 显示帧率
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow('Video Stream Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n用户中断")
        
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        elapsed = time.time() - start_time
        fps = frame_count / elapsed
        print(f"\n[统计] 总帧数: {frame_count}, 运行时间: {elapsed:.1f}s, 平均帧率: {fps:.2f} FPS")
        print("[OK] 测试完成")
        
    return True

def test_webcam():
    """测试本地摄像头"""
    print("=" * 60)
    print("本地摄像头测试")
    print("=" * 60)
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[ERROR] 无法打开本地摄像头！")
        return False
    
    print("[OK] 摄像头打开成功！")
    print("\n按 'q' 键退出窗口")
    print("=" * 60)
    
    try:
        while True:
            ret, frame = cap.read()
            
            if ret:
                cv2.imshow('Webcam Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n用户中断")
        
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[OK] 测试完成")
        
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="视频流捕获测试")
    parser.add_argument("--mode", choices=["rtmp", "webcam"], 
                       default="webcam",
                       help="测试模式: rtmp=RTMP流, webcam=本地摄像头")
    parser.add_argument("--url", type=str, 
                       default="rtmp://127.0.0.1:1935/myapp/stream",
                       help="RTMP流地址")
    
    args = parser.parse_args()
    
    if args.mode == "rtmp":
        test_rtmp_stream(args.url)
    else:
        test_webcam()
