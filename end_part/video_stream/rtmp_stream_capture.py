#!/usr/bin/env python3
"""
RTMP 视频流拉取模块
用于从 Nginx RTMP 服务器拉取视频流
支持帧率控制和图像预处理
"""

import cv2
import time
import threading
import queue
from datetime import datetime


class RTMPStreamCapture:
    """RTMP 视频流捕获器"""
    
    def __init__(self, rtmp_url='rtmp://127.0.0.1/myapp/stream', 
                 detect_fps=5, display_fps=30):
        """
        初始化 RTMP 流捕获器
        
        Args:
            rtmp_url: RTMP 流地址
            detect_fps: 检测帧率（每秒检测次数）
            display_fps: 显示帧率（用于预览）
        """
        self.rtmp_url = rtmp_url
        self.detect_fps = detect_fps
        self.display_fps = display_fps
        self.detect_interval = 1.0 / detect_fps  # 检测间隔（秒）
        self.display_interval = 1.0 / display_fps  # 显示间隔（秒）
        
        self.cap = None
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=2)  # 帧队列，最多缓存2帧
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
        # 统计信息
        self.frame_count = 0
        self.start_time = None
        
    def connect(self):
        """连接到 RTMP 流"""
        try:
            print(f"正在连接 RTMP 流: {self.rtmp_url}")
            
            # 使用 OpenCV VideoCapture 打开 RTMP 流
            self.cap = cv2.VideoCapture(self.rtmp_url)
            
            # 检查是否成功打开
            if not self.cap.isOpened():
                print(f"[ERROR] 无法打开 RTMP 流: {self.rtmp_url}")
                print("请检查:")
                print("  1. Nginx RTMP 服务器是否已启动")
                print("  2. RTMP 流地址是否正确")
                print("  3. 是否有推流端正在推送视频")
                return False
            
            # 获取视频信息
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            print(f"[OK] RTMP 流连接成功")
            print(f"  分辨率: {width}x{height}")
            print(f"  原始帧率: {fps:.2f} FPS")
            print(f"  检测帧率: {self.detect_fps} FPS")
            print(f"  检测间隔: {self.detect_interval*1000:.0f}ms")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 连接 RTMP 流时出错: {e}")
            return False
    
    def start(self):
        """开始捕获视频流"""
        if not self.connect():
            return False
        
        self.is_running = True
        self.start_time = time.time()
        
        # 启动捕获线程
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        print("[OK] 视频流捕获已启动")
        return True
    
    def _capture_loop(self):
        """视频捕获循环（在后台线程运行）"""
        while self.is_running:
            ret, frame = self.cap.read()
            
            if not ret:
                print("[WARN] 视频流读取失败，尝试重新连接...")
                time.sleep(1)
                # 尝试重新连接
                self.cap.release()
                if not self.connect():
                    time.sleep(5)
                continue
            
            self.frame_count += 1
            
            # 更新最新帧
            with self.frame_lock:
                self.latest_frame = frame.copy()
            
            # 将帧放入队列（非阻塞）
            try:
                if self.frame_queue.full():
                    self.frame_queue.get_nowait()  # 丢弃旧帧
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                pass
    
    def get_frame_for_detection(self):
        """
        获取用于检测的帧
        按照设定的 detect_fps 返回帧
        
        Returns:
            frame: OpenCV 图像帧，或 None（如果不需要检测）
        """
        if not self.is_running or self.latest_frame is None:
            return None
        
        current_time = time.time()
        
        # 检查是否到了检测时间
        if not hasattr(self, '_last_detect_time'):
            self._last_detect_time = 0
        
        if current_time - self._last_detect_time >= self.detect_interval:
            self._last_detect_time = current_time
            with self.frame_lock:
                return self.latest_frame.copy()
        
        return None
    
    def get_frame_for_display(self):
        """
        获取用于显示的帧
        按照设定的 display_fps 返回帧
        
        Returns:
            frame: OpenCV 图像帧，或 None
        """
        if not self.is_running:
            return None
        
        current_time = time.time()
        
        # 检查是否到了显示时间
        if not hasattr(self, '_last_display_time'):
            self._last_display_time = 0
        
        if current_time - self._last_display_time >= self.display_interval:
            self._last_display_time = current_time
            with self.frame_lock:
                if self.latest_frame is not None:
                    return self.latest_frame.copy()
        
        return None
    
    def get_latest_frame(self):
        """获取最新的一帧（立即返回）"""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None
    
    def get_stats(self):
        """获取统计信息"""
        if self.start_time is None:
            return {"fps": 0, "total_frames": 0, "runtime": 0}
        
        runtime = time.time() - self.start_time
        fps = self.frame_count / runtime if runtime > 0 else 0
        
        return {
            "fps": round(fps, 2),
            "total_frames": self.frame_count,
            "runtime": round(runtime, 2)
        }
    
    def stop(self):
        """停止捕获"""
        self.is_running = False
        
        if self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)
        
        if self.cap is not None:
            self.cap.release()
        
        print("[OK] 视频流捕获已停止")
        print(f"  总帧数: {self.frame_count}")
        print(f"  运行时间: {self.get_stats()['runtime']}s")


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("RTMP 视频流拉取测试")
    print("=" * 60)
    
    # 创建捕获器
    capture = RTMPStreamCapture(
        rtmp_url='rtmp://127.0.0.1/myapp/stream',
        detect_fps=5,      # 每秒检测 5 次
        display_fps=30     # 每秒显示 30 帧
    )
    
    # 开始捕获
    if not capture.start():
        print("[ERROR] 启动失败")
        exit(1)
    
    print("\n按 'q' 键退出")
    print("=" * 60)
    
    try:
        while True:
            # 获取显示帧
            display_frame = capture.get_frame_for_display()
            if display_frame is not None:
                # 显示视频
                cv2.imshow('RTMP Stream', display_frame)
            
            # 获取检测帧（用于后续 YOLO 检测）
            detect_frame = capture.get_frame_for_detection()
            if detect_frame is not None:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] 获取检测帧 - 准备进行 YOLO 检测")
                # 这里可以调用 YOLO 检测
            
            # 检查退出键
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # 显示统计信息（每5秒）
            if capture.frame_count % 150 == 0 and capture.frame_count > 0:
                stats = capture.get_stats()
                print(f"\n[统计] 实际帧率: {stats['fps']:.2f} FPS, "
                      f"总帧数: {stats['total_frames']}, "
                      f"运行时间: {stats['runtime']:.1f}s\n")
    
    except KeyboardInterrupt:
        print("\n用户中断")
    
    finally:
        capture.stop()
        cv2.destroyAllWindows()
        print("\n测试完成")
