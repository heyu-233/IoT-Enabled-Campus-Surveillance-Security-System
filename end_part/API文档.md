# IoT校园安防系统 - API文档

## 项目概述

这是一个基于Spring Boot开发的IoT校园安防系统后端API，支持用户认证、摄像头管理、告警处理、行为检测、边缘设备控制等功能。

**基础URL**: `http://localhost:8080/api`

## 目录

- [认证模块](#认证模块)
- [摄像头管理](#摄像头管理)
- [告警管理](#告警管理)
- [行为检测](#行为检测)
- [边缘设备控制](#边缘设备控制)
- [数据分析](#数据分析)
- [系统配置](#系统配置)
- [SSE实时推送](#sse实时推送)
- [数据模型](#数据模型)

---

## 认证模块

### 用户登录

**接口**: `POST /auth/login`

**描述**: 用户登录系统，获取JWT token

**请求参数**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应示例**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "ADMIN"
  }
}
```

---

### 用户注册

**接口**: `POST /auth/register`

**描述**: 新用户注册

**请求参数**:
```json
{
  "username": "string",
  "password": "string",
  "email": "string"
}
```

**响应示例**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "username": "newuser",
    "email": "newuser@example.com",
    "role": "USER"
  }
}
```

---

### 用户登出

**接口**: `POST /auth/logout`

**描述**: 用户登出系统

**需要认证**: 是

**响应**: HTTP 200 OK

---

### 获取当前用户信息

**接口**: `GET /auth/me`

**描述**: 获取当前登录用户的信息

**需要认证**: 是

**响应示例**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "ADMIN"
}
```

---

## 摄像头管理

### 获取摄像头列表

**接口**: `GET /cameras`

**描述**: 获取所有摄像头列表，支持过滤参数

**请求参数** (Query Params):
- `name`: 摄像头名称（模糊搜索）
- `location`: 位置（模糊搜索）
- `status`: 状态（online/offline）

**响应示例**:
```json
[
  {
    "id": 1,
    "name": "东门口摄像头",
    "ipAddress": "192.168.1.100",
    "port": 8080,
    "location": "学校东门",
    "status": "online",
    "streamUrl": "rtsp://192.168.1.100:554/stream",
    "lastActive": "2026-02-18T18:00:00",
    "createdAt": "2026-02-01T10:00:00",
    "updatedAt": "2026-02-18T18:00:00"
  }
]
```

---

### 获取单个摄像头详情

**接口**: `GET /cameras/{id}`

**描述**: 根据ID获取摄像头详细信息

**路径参数**:
- `id`: 摄像头ID

**响应示例**:
```json
{
  "id": 1,
  "name": "东门口摄像头",
  "ipAddress": "192.168.1.100",
  "port": 8080,
  "location": "学校东门",
  "status": "online",
  "streamUrl": "rtsp://192.168.1.100:554/stream",
  "lastActive": "2026-02-18T18:00:00",
  "createdAt": "2026-02-01T10:00:00",
  "updatedAt": "2026-02-18T18:00:00"
}
```

---

### 获取直播流地址

**接口**: `GET /cameras/{id}/stream`

**描述**: 获取摄像头的直播流地址

**路径参数**:
- `id`: 摄像头ID

**响应示例**:
```
"rtsp://192.168.1.100:554/stream"
```

---

### 刷新摄像头状态

**接口**: `POST /cameras/{id}/refresh`

**描述**: 刷新指定摄像头的在线状态

**路径参数**:
- `id`: 摄像头ID

**响应示例**:
```json
{
  "id": 1,
  "name": "东门口摄像头",
  "status": "online",
  "lastActive": "2026-02-18T18:30:00"
}
```

---

### 添加摄像头

**接口**: `POST /cameras`

**描述**: 添加新的摄像头

**需要认证**: 是

**请求参数**:
```json
{
  "name": "西门口摄像头",
  "ipAddress": "192.168.1.101",
  "port": 8080,
  "location": "学校西门",
  "streamUrl": "rtsp://192.168.1.101:554/stream"
}
```

**响应示例**:
```json
{
  "id": 2,
  "name": "西门口摄像头",
  "ipAddress": "192.168.1.101",
  "port": 8080,
  "location": "学校西门",
  "status": "offline",
  "streamUrl": "rtsp://192.168.1.101:554/stream",
  "createdAt": "2026-02-18T18:30:00",
  "updatedAt": "2026-02-18T18:30:00"
}
```

---

### 更新摄像头信息

**接口**: `PUT /cameras/{id}`

**描述**: 更新摄像头信息

**需要认证**: 是

**路径参数**:
- `id`: 摄像头ID

**请求参数**:
```json
{
  "name": "西门口摄像头（更新）",
  "location": "学校西门内"
}
```

**响应示例**:
```json
{
  "id": 2,
  "name": "西门口摄像头（更新）",
  "location": "学校西门内",
  "updatedAt": "2026-02-18T18:35:00"
}
```

---

### 删除摄像头

**接口**: `DELETE /cameras/{id}`

**描述**: 删除指定摄像头

**需要认证**: 是

**路径参数**:
- `id`: 摄像头ID

**响应**: HTTP 204 No Content

---

## 告警管理

### 获取告警列表

**接口**: `GET /alerts`

**描述**: 获取告警列表，支持过滤

**请求参数** (Query Params):
- `type`: 告警类型
- `severity`: 严重程度（high/medium/low）
- `status`: 状态（pending/processed）
- `startDate`: 开始日期
- `endDate`: 结束日期

**响应示例**:
```json
[
  {
    "id": 1,
    "behaviorId": 1,
    "type": "intrusion",
    "severity": "high",
    "status": "pending",
    "description": "检测到人员入侵",
    "processedBy": null,
    "processingNotes": null,
    "processedAt": null,
    "createdAt": "2026-02-18T18:00:00",
    "screenshot": "/screenshots/alert_1.jpg"
  }
]
```

---

### 获取单个告警详情

**接口**: `GET /alerts/{id}`

**描述**: 根据ID获取告警详情

**路径参数**:
- `id`: 告警ID

**响应示例**:
```json
{
  "id": 1,
  "behaviorId": 1,
  "type": "intrusion",
  "severity": "high",
  "status": "pending",
  "description": "检测到人员入侵",
  "createdAt": "2026-02-18T18:00:00",
  "screenshot": "/screenshots/alert_1.jpg"
}
```

---

### 处理告警

**接口**: `POST /alerts/{id}/process`

**描述**: 标记告警为已处理

**需要认证**: 是

**路径参数**:
- `id`: 告警ID

**请求参数**:
```json
{
  "processingNotes": "已核实，误报"
}
```

**响应示例**:
```json
{
  "id": 1,
  "status": "processed",
  "processedBy": "admin",
  "processingNotes": "已核实，误报",
  "processedAt": "2026-02-18T18:30:00"
}
```

---

### 搜索告警

**接口**: `GET /alerts/search`

**描述**: 搜索告警记录

**请求参数** (Query Params):
- `keyword`: 关键词
- `type`: 告警类型
- `severity`: 严重程度

**响应示例**:
```json
[
  {
    "id": 1,
    "type": "intrusion",
    "description": "检测到人员入侵",
    "createdAt": "2026-02-18T18:00:00"
  }
]
```

---

### 创建告警

**接口**: `POST /alerts`

**描述**: 手动创建告警

**需要认证**: 是

**请求参数**:
```json
{
  "type": "intrusion",
  "severity": "high",
  "description": "手动创建的告警",
  "screenshot": "/screenshots/manual.jpg"
}
```

**响应示例**:
```json
{
  "id": 2,
  "type": "intrusion",
  "severity": "high",
  "status": "pending",
  "description": "手动创建的告警",
  "createdAt": "2026-02-18T18:40:00"
}
```

---

## 行为检测

### 获取行为记录列表

**接口**: `GET /behaviors`

**描述**: 获取行为检测记录列表

**请求参数** (Query Params):
- `cameraId`: 摄像头ID
- `type`: 行为类型
- `startDate`: 开始日期
- `endDate`: 结束日期

**响应示例**:
```json
[
  {
    "id": 1,
    "cameraId": 1,
    "type": "intrusion",
    "description": "检测到入侵行为",
    "imageUrl": "/images/behavior_1.jpg",
    "confidence": 0.95,
    "occurredAt": "2026-02-18T18:00:00",
    "createdAt": "2026-02-18T18:00:00"
  }
]
```

---

### 获取单个行为记录详情

**接口**: `GET /behaviors/{id}`

**描述**: 根据ID获取行为记录详情

**路径参数**:
- `id`: 行为记录ID

**响应示例**:
```json
{
  "id": 1,
  "cameraId": 1,
  "type": "intrusion",
  "description": "检测到入侵行为",
  "imageUrl": "/images/behavior_1.jpg",
  "confidence": 0.95,
  "occurredAt": "2026-02-18T18:00:00"
}
```

---

### 删除行为记录

**接口**: `DELETE /behaviors/{id}`

**描述**: 删除指定行为记录

**需要认证**: 是

**路径参数**:
- `id`: 行为记录ID

**响应**: HTTP 204 No Content

---

### 添加行为记录

**接口**: `POST /behaviors`

**描述**: 添加行为检测记录

**需要认证**: 是

**请求参数**:
```json
{
  "cameraId": 1,
  "type": "loitering",
  "description": "检测到人员徘徊",
  "imageUrl": "/images/behavior_2.jpg",
  "confidence": 0.88,
  "occurredAt": "2026-02-18T18:45:00"
}
```

**响应示例**:
```json
{
  "id": 2,
  "cameraId": 1,
  "type": "loitering",
  "description": "检测到人员徘徊",
  "confidence": 0.88,
  "occurredAt": "2026-02-18T18:45:00",
  "createdAt": "2026-02-18T18:45:00"
}
```

---

## 边缘设备控制

### 启动检测

**接口**: `GET|POST /edge/control/start`

**描述**: 向边缘设备发送启动检测指令

**请求参数** (Query Params):
- `deviceId`: 设备ID

**响应示例**:
```
"启动检测指令已发送到设备: edge-camera-001"
```

**MQTT主题**: `edge/control/start`

**MQTT消息**:
```json
{
  "command": "start",
  "device_id": "edge-camera-001"
}
```

---

### 停止检测

**接口**: `GET|POST /edge/control/stop`

**描述**: 向边缘设备发送停止检测指令

**请求参数** (Query Params):
- `deviceId`: 设备ID

**响应示例**:
```
"停止检测指令已发送到设备: edge-camera-001"
```

**MQTT主题**: `edge/control/stop`

**MQTT消息**:
```json
{
  "command": "stop",
  "device_id": "edge-camera-001"
}
```

---

### 更新配置

**接口**: `GET|POST /edge/control/config`

**描述**: 向边缘设备发送配置更新

**请求参数** (Query Params):
- `deviceId`: 设备ID

**请求体** (可选): 配置JSON

**响应示例**:
```
"配置已发送到设备: edge-camera-001"
```

**MQTT主题**: `edge/control/config`

---

### MQTT消息订阅

后端会订阅以下MQTT主题来接收边缘设备的消息：

| 主题 | 描述 |
|------|------|
| `edge/detection/#` | 检测结果 |
| `edge/alerts/#` | 边缘告警 |
| `sensors/#` | 传感器数据 |
| `alerts/#` | 告警数据 |
| `edge/heartbeat` | 设备心跳 |

---

## 数据分析

### 告警类型分布

**接口**: `GET /analytics/type-distribution`

**描述**: 获取告警类型分布统计

**请求参数** (Query Params):
- `startDate`: 开始日期
- `endDate`: 结束日期

**响应示例**:
```json
{
  "intrusion": 15,
  "loitering": 8,
  "fighting": 3,
  "other": 2
}
```

---

### 每日告警统计

**接口**: `GET /analytics/daily-alerts`

**描述**: 获取每日告警数量统计

**请求参数** (Query Params):
- `startDate`: 开始日期
- `endDate`: 结束日期

**响应示例**:
```json
{
  "2026-02-15": 5,
  "2026-02-16": 8,
  "2026-02-17": 10,
  "2026-02-18": 7
}
```

---

### 区域热力图

**接口**: `GET /analytics/area-heatmap`

**描述**: 获取各区域告警热力图数据

**请求参数** (Query Params):
- `startDate`: 开始日期
- `endDate`: 结束日期

**响应示例**:
```json
{
  "学校东门": 25,
  "学校西门": 12,
  "教学楼": 8,
  "宿舍楼": 15
}
```

---

### 类型详情

**接口**: `GET /analytics/types/{type}`

**描述**: 获取指定告警类型的详细统计

**路径参数**:
- `type`: 告警类型

**请求参数** (Query Params):
- `startDate`: 开始日期
- `endDate`: 结束日期

**响应示例**:
```json
{
  "type": "intrusion",
  "total": 15,
  "byCamera": {
    "1": 8,
    "2": 5,
    "3": 2
  },
  "byHour": {
    "0": 2,
    "1": 1,
    "2": 3,
    "3": 2
  }
}
```

---

## 系统配置

### 获取告警设置

**接口**: `GET /config/alert-settings`

**描述**: 获取系统告警设置

**响应示例**:
```json
{
  "id": 1,
  "emailEnabled": true,
  "smsEnabled": false,
  "confidenceThreshold": 0.8,
  "autoAlertEnabled": true,
  "updatedAt": "2026-02-18T10:00:00"
}
```

---

### 更新告警设置

**接口**: `PUT /config/alert-settings`

**描述**: 更新系统告警设置

**需要认证**: 是

**请求参数**:
```json
{
  "emailEnabled": true,
  "smsEnabled": true,
  "confidenceThreshold": 0.85,
  "autoAlertEnabled": true
}
```

**响应示例**:
```json
{
  "id": 1,
  "emailEnabled": true,
  "smsEnabled": true,
  "confidenceThreshold": 0.85,
  "autoAlertEnabled": true,
  "updatedAt": "2026-02-18T18:50:00"
}
```

---

## SSE实时推送

### 订阅行为事件流

**接口**: `GET /behaviors/stream`

**描述**: 订阅SSE实时推送的行为检测事件

**Content-Type**: `text/event-stream`

**事件格式**:
```
data: {"id": 1, "type": "intrusion", "cameraId": 1, "confidence": 0.95, "occurredAt": "2026-02-18T18:00:00"}
```

---

## 数据模型

### User（用户）

```json
{
  "id": "Long",
  "username": "String",
  "password": "String",
  "email": "String",
  "role": "String",
  "createdAt": "LocalDateTime",
  "updatedAt": "LocalDateTime"
}
```

### Camera（摄像头）

```json
{
  "id": "Long",
  "name": "String",
  "ipAddress": "String",
  "port": "Integer",
  "location": "String",
  "status": "String (online/offline)",
  "streamUrl": "String",
  "lastActive": "LocalDateTime",
  "createdAt": "LocalDateTime",
  "updatedAt": "LocalDateTime"
}
```

### Alert（告警）

```json
{
  "id": "Long",
  "behaviorId": "Long",
  "type": "String",
  "severity": "String (high/medium/low)",
  "status": "String (pending/processed)",
  "description": "String",
  "processedBy": "String",
  "processingNotes": "String",
  "processedAt": "LocalDateTime",
  "createdAt": "LocalDateTime",
  "screenshot": "String"
}
```

### Behavior（行为检测）

```json
{
  "id": "Long",
  "cameraId": "Long",
  "type": "String",
  "description": "String",
  "imageUrl": "String",
  "confidence": "Double",
  "occurredAt": "LocalDateTime",
  "createdAt": "LocalDateTime"
}
```

### LoginRequest（登录请求）

```json
{
  "username": "String",
  "password": "String"
}
```

### RegisterRequest（注册请求）

```json
{
  "username": "String",
  "password": "String",
  "email": "String"
}
```

### AuthResponse（认证响应）

```json
{
  "token": "String (JWT)",
  "user": "UserDto"
}
```

---

## 认证说明

### JWT认证

除了以下端点外，其他所有端点都需要JWT认证：
- `POST /auth/login`
- `POST /auth/register`
- `GET /alerts`
- `GET /behaviors`
- `/edge/**`

### 使用方式

在请求头中添加：
```
Authorization: Bearer {your_jwt_token}
```

---

## 错误响应

### 通用错误格式

```json
{
  "timestamp": "2026-02-18T18:00:00.000Z",
  "message": "错误描述",
  "details": "uri=/api/endpoint"
}
```

### 常见HTTP状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无内容） |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## MQTT配置

### Broker配置

在 `application.properties` 中配置：

```properties
mqtt.broker.url=tcp://192.168.1.103:1883
mqtt.client.id=backend-client
mqtt.topic.sensors=sensors/+
mqtt.topic.alerts=alerts/+
mqtt.topic.edge=edge/#
mqtt.qos=1
```

### 主题规范

| 主题模式 | 方向 | 说明 |
|---------|------|------|
| `edge/control/start` | 后端→边缘 | 启动检测指令 |
| `edge/control/stop` | 后端→边缘 | 停止检测指令 |
| `edge/control/config` | 后端→边缘 | 配置更新 |
| `edge/detection/results` | 边缘→后端 | 检测结果 |
| `edge/alerts/urgent` | 边缘→后端 | 紧急告警 |
| `edge/heartbeat` | 边缘→后端 | 设备心跳 |

---

## 项目结构

```
end_part/
├── src/main/java/com/example/end_part/
│   ├── controller/          # 控制器层
│   │   ├── AuthController.java
│   │   ├── CameraController.java
│   │   ├── AlertController.java
│   │   ├── BehaviorController.java
│   │   ├── EdgeController.java
│   │   ├── AnalyticsController.java
│   │   ├── ConfigController.java
│   │   └── SseController.java
│   ├── service/             # 服务层
│   ├── mapper/              # 数据访问层
│   ├── entity/              # 实体类
│   ├── dto/                 # 数据传输对象
│   ├── config/              # 配置类
│   │   ├── MqttConfig.java
│   │   ├── SecurityConfig.java
│   │   └── WebSocketConfig.java
│   └── utils/               # 工具类
└── src/main/resources/
    ├── application.properties
    └── db/init.sql
```

---

## 更新日志

### v1.0.0 (2026-02-18)
- 初始版本发布
- 实现用户认证模块
- 实现摄像头管理
- 实现告警管理
- 实现行为检测
- 集成MQTT边缘设备控制
- 添加数据分析功能
- 支持SSE实时推送
