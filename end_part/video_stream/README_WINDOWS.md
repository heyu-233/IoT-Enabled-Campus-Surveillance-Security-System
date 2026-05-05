# Windows 版 YOLO 推理服务部署指南

## 概述

本项目将 YOLOv8 推理服务从 Ubuntu 迁移到 Windows，简化架构并提高性能。

## 架构图

```
┌─────────────┐
│  开发板      │─────── RTMP 推流 ───────┐
└─────────────┘                            │
                                          ▼
┌─────────────┐                    ┌─────────────────┐
│  前端        │◀─── 直接拉取 RTMP ───│  Nginx RTMP     │
│  (Vue3)      │      流播放          │  服务器(Windows)│
└─────────────┘                    └─────────────────┘
       │                                       │
       │  接收检测结果和告警                    │ 拉取流检测
       ▼                                       ▼
┌─────────────┐                    ┌─────────────────┐
│  Spring Boot │ ◀───── MQTT ──────│  YOLO推理服务    │
│  后端        │      (Windows)     │  (Windows)       │
└─────────────┘                    └─────────────────┘
```

## 部署步骤

### 第一步：安装 Windows 版 Mosquitto

1. 从 https://mosquitto.org/download/ 下载 Windows 安装包
2. 安装后，打开命令行，启动 Mosquitto：

```powershell
# 启动 Mosquitto
mosquitto -v
```

### 第二步：准备 YOLO 模型

将你的 `best.pt` 模型文件放到 `video_stream` 目录下。

### 第三步：安装 Python 依赖

```powershell
cd video_stream
pip install ultralytics opencv-python paho-mqtt numpy
```

### 第四步：启动后端

```powershell
cd ..
mvn spring-boot:run
```

### 第五步：启动 YOLO 推理服务

```powershell
cd video_stream

# 使用默认配置启动
python yolo_inference_windows.py

# 或者自定义参数启动
python yolo_inference_windows.py --rtmp rtmp://127.0.0.1/myapp/stream --mqtt 127.0.0.1 --model best.pt --fps 5
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--rtmp` | RTMP 流地址 | `rtmp://127.0.0.1/myapp/stream` |
| `--mqtt` | MQTT Broker 地址 | `127.0.0.1` |
| `--port` | MQTT 端口 | `1883` |
| `--model` | YOLO 模型路径 | `best.pt` |
| `--fps` | 检测帧率 | `5` |
| `--device` | 设备ID | `windows-edge-001` |

## 测试 RTMP 视频流

```powershell
# 仅测试连接
python test_rtmp.py --mode connect

# 带显示测试
python test_rtmp.py --mode display
```

## 验证流程

1. ✅ 启动 Mosquitto：`mosquitto -v`
2. ✅ 启动 Nginx RTMP 服务器
3. ✅ 开发板开始推流到 Nginx
4. ✅ 启动后端：`mvn spring-boot:run`
5. ✅ 启动推理服务：`python yolo_inference_windows.py`
6. ✅ 前端直接从 Nginx 拉取 RTMP 流播放
7. ✅ 推理服务检测到目标后，通过 MQTT 发送给后端
8. ✅ 后端通过 WebSocket 推送给前端显示告警

## 文件说明

- `rtmp_stream_capture.py` - RTMP 视频流捕获模块
- `yolo_inference_windows.py` - YOLO 推理服务（Windows版）
- `test_rtmp.py` - RTMP 流测试脚本
- `README_WINDOWS.md` - 本说明文档

## 注意事项

1. 确保 Nginx RTMP 服务器已启动并有推流
2. 确保 Mosquitto 已启动
3. 确保后端已启动
4. 确保 YOLO 模型文件存在
5. 按 `q` 键可以退出推理服务
