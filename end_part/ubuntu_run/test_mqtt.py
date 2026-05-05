#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ 测试客户端连接成功")
        client.subscribe("edge/#")
        print("✓ 已订阅边缘设备主题")
    else:
        print(f"✗ 连接失败，返回码: {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"\n📥 收到消息:")
    print(f"   主题: {topic}")
    print(f"   内容: {payload}")

def on_publish(client, userdata, mid):
    print(f"✓ 测试消息发送成功，ID: {mid}")

# 创建测试客户端
client = mqtt.Client(client_id="test-client")
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish

# 连接
broker_url = "192.168.1.103"  # 修改为你的MQTT broker地址
print(f"🔗 连接到MQTT Broker: {broker_url}")
client.connect(broker_url, 1883, 60)
client.loop_start()

# 等待连接
time.sleep(2)

# 发送测试消息
print("\n📤 发送测试消息...")
test_message = {
    "test": True,
    "message": "这是测试消息",
    "timestamp": int(time.time())
}
client.publish("edge/test", json.dumps(test_message))

# 发送启动指令
print("📤 发送启动指令...")
start_command = {
    "command": "start",
    "device_id": "edge-camera-001"
}
client.publish("edge/control/start", json.dumps(start_command))

# 保持运行
print("\n💡 监听消息中... (按 Ctrl+C 退出)")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n👋 测试客户端退出")
finally:
    client.loop_stop()
    client.disconnect()
