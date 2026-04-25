#!/usr/bin/env python3
"""
测试发送单张图片到后端
"""

import paho.mqtt.client as mqtt
import base64
import json
import time
import os
from datetime import datetime

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "edge/detection/results"
MQTT_CLIENT_ID = "test-image-sender"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[OK] MQTT 连接成功！")
    else:
        print(f"[ERROR] MQTT 连接失败，返回码: {rc}")

def on_publish(client, userdata, mid):
    print(f"[OK] 消息发送成功，ID: {mid}")

def send_image(image_path):
    print("=" * 60)
    print("单张图片发送测试")
    print("=" * 60)
    
    if not os.path.exists(image_path):
        print(f"[ERROR] 图片文件不存在: {image_path}")
        return False
    
    print(f"\n[INFO] 找到图片: {image_path}")
    
    try:
        client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        client.on_connect = on_connect
        client.on_publish = on_publish
        
        print(f"\n[INFO] 正在连接 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        time.sleep(1)
        
        print(f"\n[INFO] 读取图片...")
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        print(f"[INFO] 编码图片...")
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        print(f"[OK] 图片编码成功，大小: {len(image_base64)} 字符")
        
        payload = {
            "device_id": "test-device-001",
            "timestamp": datetime.now().isoformat(),
            "event_type": "fire",
            "confidence": 0.85,
            "bbox": [100, 100, 300, 300],
            "image": image_base64
        }
        
        payload_json = json.dumps(payload, ensure_ascii=False)
        
        print(f"\n[INFO] 发送图片到主题: {MQTT_TOPIC}")
        result = client.publish(MQTT_TOPIC, payload_json, qos=1)
        result.wait_for_publish()
        
        time.sleep(2)
        
        print("\n" + "=" * 60)
        print("[OK] 图片发送成功！")
        print("=" * 60)
        
        client.loop_stop()
        client.disconnect()
        print("\n[OK] 连接已断开")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="发送单张图片测试")
    parser.add_argument("--image", type=str, required=True, help="图片文件路径")
    
    args = parser.parse_args()
    
    send_image(args.image)
