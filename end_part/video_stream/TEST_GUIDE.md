# 完整系统测试指南

## 测试前准备

### 检查清单

- [ ] Windows 版 Mosquitto 已安装
- [ ] Nginx RTMP 服务器已启动
- [ ] 开发板正在推流到 Nginx
- [ ] best.pt 模型文件已放到 video_stream 目录
- [ ] Python 依赖已安装
- [ ] MySQL 数据库已启动

---

## 分步骤测试

### 第一步：测试 MQTT Broker

1. **启动 Mosquitto**
   ```powershell
   mosquitto -v
   ```

2. **测试 MQTT 连接**（新开一个 PowerShell）
   ```powershell
   cd video_stream
   python test_mqtt.py
   ```

### 第二步：测试 RTMP 视频流

1. **确保开发板正在推流到 Nginx**
   - 推流地址：`rtmp://127.0.0.1/myapp/stream`

2. **测试 RTMP 连接**
   ```powershell
   cd video_stream
   python test_rtmp.py --mode connect
   ```

3. **测试 RTMP 显示**
   ```powershell
   python test_rtmp.py --mode display
   ```
   应该能看到视频窗口播放！

### 第三步：启动后端

```powershell
cd ..
mvn spring-boot:run
```

等待看到：
```
Started EndPartApplication in X seconds
Tomcat started on port(s): 8080 (http)
```

### 第四步：启动 YOLO 推理服务

```powershell
cd video_stream
python yolo_inference_windows.py --model best.pt --fps 5
```

应该看到：
```
============================================================
YOLOv8 推理服务 (Windows版)
============================================================
正在加载 YOLO 模型: best.pt
✓ 模型加载成功
正在连接 MQTT Broker: 127.0.0.1:1883
✓ MQTT 连接成功
正在连接 RTMP 流: rtmp://127.0.0.1/myapp/stream
✓ RTMP 流连接成功
✓ 推理服务已启动，按 'q' 键退出
============================================================
```

### 第五步：测试完整链路

当 YOLO 检测到目标时，应该看到：
```
[10:30:45.123] 检测到 2 个目标
📸 图片已编码，大小: 123456 字符
📤 检测结果已发送到 edge/detection/results
```

同时后端日志应该显示：
```
收到MQTT消息 - 主题: edge/detection/results
处理来自设备 windows-edge-001 的检测结果，检测到 2 个目标
检测图片已保存: /images/detection/xxx.jpg
行为记录已保存: fire - 置信度: 0.92 - ID: 1
自动告警已创建: fire - 严重程度: HIGH - ID: 1
```

---

## 问题排查

### 问题1：Mosquitto 启动失败
**症状**：`Address already in use`
**解决**：
```powershell
# 查找占用端口的进程
netstat -ano | findstr :1883
# 结束进程（替换 PID）
taskkill /PID <PID> /F
```

### 问题2：RTMP 连接失败
**症状**：`无法打开 RTMP 流`
**检查**：
1. Nginx RTMP 服务器是否启动
2. 开发板是否正在推流
3. 推流地址是否正确

### 问题3：MQTT 连接失败
**症状**：`MQTT 连接失败`
**检查**：
1. Mosquitto 是否启动
2. 防火墙是否允许 1883 端口
3. `application.properties` 中的配置是否正确

### 问题4：后端启动失败
**症状**：数据库连接错误
**检查**：
1. MySQL 是否启动
2. 数据库用户名密码是否正确
3. 数据库 `qgg_backend` 是否存在

---

## 端到端测试验证

### 验证1：视频流播放
- ✅ 前端能直接从 Nginx 拉取 RTMP 流播放

### 验证2：YOLO 检测
- ✅ YOLO 推理服务能从 Nginx 拉取 RTMP 流
- ✅ YOLO 能检测到目标
- ✅ 检测结果通过 MQTT 发送

### 验证3：后端处理
- ✅ 后端收到 MQTT 消息
- ✅ 图片保存成功
- ✅ 行为记录保存到数据库
- ✅ 告警创建成功

### 验证4：前端告警
- ✅ 前端收到 WebSocket 告警
- ✅ 告警信息正确显示
- ✅ 检测图片能正常显示
