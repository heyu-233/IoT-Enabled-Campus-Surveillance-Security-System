#!/usr/bin/env python3
"""
简单的 YOLO 测试脚本
使用官方 YOLOv8 模型测试推理功能
"""

import cv2
from ultralytics import YOLO
import time

def test_yolo_on_image(image_path):
    """在单张图片上测试 YOLO"""
    print("=" * 60)
    print("YOLO 单张图片测试")
    print("=" * 60)
    
    # 加载模型
    print("\n[INFO] 加载 YOLO 模型...")
    try:
        if __import__('os').path.exists('best.pt'):
            model = YOLO('best.pt')
            print("[OK] 使用自定义模型 best.pt 加载成功！")
        else:
            model = YOLO('yolov8n.pt')
            print("[WARN] best.pt 不存在，使用官方 YOLOv8n 模型")
        print("[OK] 模型加载成功！")
    except Exception as e:
        print(f"[ERROR] 模型加载失败: {e}")
        return False
    
    # 读取图片
    print(f"\n[INFO] 读取图片: {image_path}")
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"[ERROR] 无法读取图片: {image_path}")
        return False
    
    print(f"[OK] 图片读取成功，尺寸: {frame.shape}")
    
    # 运行检测
    print("\n[INFO] 运行 YOLO 检测...")
    start_time = time.time()
    results = model(frame, verbose=False)
    elapsed = time.time() - start_time
    print(f"[OK] 检测完成，耗时: {elapsed*1000:.1f} ms")
    
    # 处理结果
    detections = []
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                cls_name = model.names[cls_id]
                
                detections.append({
                    "class": cls_name,
                    "confidence": conf,
                    "bbox": xyxy
                })
    
    print(f"\n[检测结果] 共检测到 {len(detections)} 个目标:")
    for i, det in enumerate(detections, 1):
        print(f"  {i}. {det['class']} (置信度: {det['confidence']:.2f})")
    
    # 在图片上画框
    annotated_frame = results[0].plot()
    
    # 显示结果
    print("\n[INFO] 显示检测结果（按任意键关闭窗口）")
    cv2.imshow("YOLO Detection Result", annotated_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # 保存结果
    output_path = "yolo_result.jpg"
    cv2.imwrite(output_path, annotated_frame)
    print(f"\n[OK] 结果已保存到: {output_path}")
    
    return True

def test_yolo_on_stream(rtmp_url):
    """在视频流上测试 YOLO"""
    print("=" * 60)
    print("YOLO 视频流测试")
    print("=" * 60)
    
    # 加载模型
    print("\n[INFO] 加载 YOLO 模型...")
    try:
        if __import__('os').path.exists('best.pt'):
            model = YOLO('best.pt')
            print("[OK] 使用自定义模型 best.pt 加载成功！")
        else:
            model = YOLO('yolov8n.pt')
            print("[WARN] best.pt 不存在，使用官方 YOLOv8n 模型")
        print("[OK] 模型加载成功！")
    except Exception as e:
        print(f"[ERROR] 模型加载失败: {e}")
        return False
    
    # 打开流
    print(f"\n[INFO] 连接视频流: {rtmp_url}")
    cap = cv2.VideoCapture(rtmp_url)
    
    if not cap.isOpened():
        print("[ERROR] 无法打开视频流！")
        return False
    
    print("[OK] 流连接成功！")
    print("\n按 'q' 键退出")
    print("=" * 60)
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("[WARN] 读取帧失败")
                time.sleep(1)
                continue
            
            # 运行检测
            results = model(frame, verbose=False)
            
            # 画框
            annotated_frame = results[0].plot()
            
            # 显示帧率
            frame_count += 1
            elapsed = time.time() - start_time
            if frame_count % 30 == 0:
                fps = frame_count / elapsed
                cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow("YOLO Stream Detection", annotated_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n用户中断")
        
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        elapsed = time.time() - start_time
        fps = frame_count / elapsed
        print(f"\n[统计] 总帧数: {frame_count}, 平均帧率: {fps:.2f} FPS")
        print("[OK] 测试完成")
    
    return True

if __name__ == "__main__":
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="YOLO 简单测试")
    parser.add_argument("--mode", choices=["image", "stream"], 
                       default="image",
                       help="测试模式: image=单张图片, stream=视频流")
    parser.add_argument("--input", type=str, 
                       default="captured_frame.jpg",
                       help="输入: 图片路径 或 RTMP 地址")
    
    args = parser.parse_args()
    
    if args.mode == "image":
        if os.path.exists(args.input):
            test_yolo_on_image(args.input)
        else:
            print(f"[ERROR] 图片文件不存在: {args.input}")
            print("请先运行 capture_single_frame.py 捕获一张图片")
    else:
        test_yolo_on_stream(args.input)
