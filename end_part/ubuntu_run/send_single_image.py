#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
import os
import base64
import cv2

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("鉁?MQTT杩炴帴鎴愬姛")
    else:
        print(f"鉁?MQTT杩炴帴澶辫触锛岃繑鍥炵爜: {rc}")

def on_publish(client, userdata, mid):
    print(f"鉁?娑堟伅鍙戦€佹垚鍔燂紝ID: {mid}")

def image_to_base64(image_path):
    """灏嗗浘鐗囨枃浠惰浆鎹负Base64瀛楃涓?""
    try:
        # 浣跨敤OpenCV璇诲彇鍥剧墖
        img = cv2.imread(image_path)
        if img is None:
            print(f"鉁?鏃犳硶璇诲彇鍥剧墖: {image_path}")
            return None

        # 缂栫爜涓篔PEG
        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
        # 杞崲涓築ase64
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return image_base64
    except Exception as e:
        print(f"鉁?鍥剧墖缂栫爜澶辫触: {e}")
        return None

def send_single_image(broker_url, broker_port, image_path, device_id='test-device'):
    """鍙戦€佸崟寮犲浘鐗囧埌鍚庣"""

    # 鍒涘缓MQTT瀹㈡埛绔?    client = mqtt.Client(client_id="single-image-sender")
    client.on_connect = on_connect
    client.on_publish = on_publish

    # 杩炴帴鍒癕QTT broker
    print(f"馃敆 杩炴帴鍒癕QTT Broker: {broker_url}:{broker_port}")
    try:
        client.connect(broker_url, broker_port, 60)
        client.loop_start()
    except Exception as e:
        print(f"鉁?MQTT杩炴帴澶辫触: {e}")
        return

    # 绛夊緟杩炴帴寤虹珛
    time.sleep(2)

    # 妫€鏌ュ浘鐗囨槸鍚﹀瓨鍦?    if not os.path.exists(image_path):
        print(f"鉁?鍥剧墖鏂囦欢涓嶅瓨鍦? {image_path}")
        client.loop_stop()
        client.disconnect()
        return

    print(f"馃摲 璇诲彇鍥剧墖: {image_path}")

    # 杞崲鍥剧墖涓築ase64
    image_base64 = image_to_base64(image_path)
    if not image_base64:
        client.loop_stop()
        client.disconnect()
        return

    print(f"鉁?鍥剧墖缂栫爜鎴愬姛锛屽ぇ灏? {len(image_base64)} 瀛楃")

    # 鏋勫缓娑堟伅
    message = {
        "device_id": device_id,
        "timestamp": int(time.time()),
        "image": image_base64,
        "detections": [
            {
                "class": "test_detection",
                "confidence": 0.95
            }
        ]
    }

    # 鍙戦€佹秷鎭?    topic = "edge/detection/results"
    payload = json.dumps(message, ensure_ascii=False)

    print(f"馃摛 鍙戦€佸浘鐗囧埌涓婚: {topic}")
    try:
        result = client.publish(topic, payload, qos=1)
        result.wait_for_publish()

        if result.is_published():
            print("鉁?鍥剧墖鍙戦€佹垚鍔燂紒")
        else:
            print("鉁?鍥剧墖鍙戦€佸け璐?)
    except Exception as e:
        print(f"鉁?鍙戦€佹秷鎭椂鍑洪敊: {e}")

    # 绛夊緟涓€涓嬪啀鏂紑
    time.sleep(2)

    # 鏂紑杩炴帴
    client.loop_stop()
    client.disconnect()
    print("鉁?杩炴帴宸叉柇寮€")

# 涓荤▼搴?if __name__ == "__main__":
    print("=" * 60)
    print("鍗曞紶鍥剧墖鍙戦€佹祴璇?)
    print("=" * 60)

    # 閰嶇疆
    BROKER_URL = "192.168.1.103"  # MQTT broker鍦板潃
    BROKER_PORT = 1883
    DEVICE_ID = "test-camera-001"

    # 鍥剧墖璺緞 - 鏍规嵁浣犵殑瀹為檯鎯呭喌淇敼
    # 浣犲彲浠ヤ慨鏀硅繖閲屾潵鎸囧畾瑕佸彂閫佺殑鍥剧墖
    RESULTS_DIR = "/home/maomao/yolo_project/results"

    # 鏌ユ壘results鏂囦欢澶逛腑鐨勭涓€寮犲浘鐗?    image_path = None
    if os.path.exists(RESULTS_DIR):
        for filename in os.listdir(RESULTS_DIR):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(RESULTS_DIR, filename)
                break

    if not image_path:
        print(f"鉁?鍦?{RESULTS_DIR} 涓湭鎵惧埌鍥剧墖鏂囦欢")
        print("\n馃挕 鎻愮ず: 璇蜂慨鏀硅剼鏈腑鐨?image_path 鍙橀噺锛屾寚瀹氳鍙戦€佺殑鍥剧墖璺緞")
        print("   渚嬪:")
        print('   image_path = "/home/maomao/yolo_project/results/test_image.jpg"')
    else:
        print(f"鉁?鎵惧埌鍥剧墖: {image_path}")
        print()

        # 鍙戦€佸浘鐗?        send_single_image(BROKER_URL, BROKER_PORT, image_path, DEVICE_ID)
