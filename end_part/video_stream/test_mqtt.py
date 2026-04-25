#!/usr/bin/env python3
"""
MQTT 连接测试脚本
"""

import paho.mqtt.client as mqtt
import time
import json

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[OK] MQTT 连接成功！")
        client.subscribe("edge/#")
        print("[OK] 已订阅主题: edge/#")
    else:
        print(f"[ERROR] MQTT 连接失败，返回码: {rc}")

def on_message(client, userdata, msg):
    print(f"\n[IN] 收到消息 - 主题: {msg.topic}")
    print(f"     内容: {msg.payload.decode()}")

def on_publish(client, userdata, mid):
    print(f"[OUT] 消息发送成功，ID: {mid}")

def test_mqtt():
    print("=" * 60)
    print("MQTT 连接测试")
    print("=" * 60)
    
    client = mqtt.Client(client_id="test-client")
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    
    try:
        print("正在连接 MQTT Broker: 127.0.0.1:1883")
        client.connect("127.0.0.1", 1883, 60)
        client.loop_start()
        
        time.sleep(1)
        
        # 发送测试消息
        test_message = {
            "device_id": "test-device",
            "timestamp": int(time.time()),
            "message": "Hello from test script!"
        }
        
        print(f"\n发送测试消息到主题: edge/test")
        client.publish("edge/test", json.dumps(test_message), qos=1)
        
        print("\n等待消息... (按 Ctrl+C 退出)")
        print("=" * 60)
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"[ERROR] 错误: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("[OK] 已断开连接")

if __name__ == "__main__":
    test_mqtt()
