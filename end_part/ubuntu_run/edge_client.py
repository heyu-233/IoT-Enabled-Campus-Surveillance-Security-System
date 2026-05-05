#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
import os
import cv2
import base64
from ultralytics import YOLO

class EdgeComputingClient:
    def __init__(self, broker_url='localhost', broker_port=1883,
                 client_id='edge-client-ubuntu'):
        self.broker_url = broker_url
        self.broker_port = broker_port
        self.client_id = client_id
        self.client = None
        self.model = None
        self.is_running = False

        # 浣跨敤鐜版湁鐨勬ā鍨嬫枃浠?        self.model_path = '/home/maomao/yolo_project/best.pt'

        # 鍒濆鍖朰OLOv8妯″瀷
        self.load_model()

        # 鍒濆鍖朚QTT瀹㈡埛绔?        self.init_mqtt()

    def load_model(self):
        """鍔犺浇YOLOv8妯″瀷"""
        try:
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                print(f"鉁?浣跨敤鐜版湁YOLO妯″瀷: {self.model_path}")
            else:
                print(f"鈿?妯″瀷鏂囦欢涓嶅瓨鍦? {self.model_path}")
                print("灏濊瘯浣跨敤榛樿妯″瀷...")
                self.model = YOLO('yolov8n.pt')
                print("鉁?浣跨敤榛樿YOLOv8妯″瀷")
        except Exception as e:
            print(f"鉁?妯″瀷鍔犺浇澶辫触: {e}")
            import sys
            sys.exit(1)

    def init_mqtt(self):
        """鍒濆鍖朚QTT瀹㈡埛绔?""
        self.client = mqtt.Client(client_id=self.client_id)

        # 璁剧疆鍥炶皟鍑芥暟
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect

        # 杩炴帴鍒癕QTT broker
        try:
            print(f"姝ｅ湪杩炴帴鍒癕QTT Broker: {self.broker_url}:{self.broker_port}")
            self.client.connect(self.broker_url, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"鉁?MQTT杩炴帴澶辫触: {e}")
            import sys
            sys.exit(1)

    def on_connect(self, client, userdata, flags, rc):
        """杩炴帴鍥炶皟"""
        if rc == 0:
            print("鉁?MQTT杩炴帴鎴愬姛")
            # 璁㈤槄鎺у埗鎸囦护涓婚
            client.subscribe("edge/control/+")
            print("鉁?宸茶闃呮帶鍒舵寚浠や富棰?)
        else:
            print(f"鉁?MQTT杩炴帴澶辫触锛岃繑鍥炵爜: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """鏂紑杩炴帴鍥炶皟"""
        if rc != 0:
            print(f"鈿?MQTT鎰忓鏂紑锛屽皾璇曢噸鏂拌繛鎺?..")

    def on_message(self, client, userdata, msg):
        """鎺ユ敹娑堟伅鍥炶皟"""
        topic = msg.topic
        payload = msg.payload.decode()

        print(f"\n馃摜 鏀跺埌娑堟伅 - 涓婚: {topic}")
        print(f"   鍐呭: {payload}")

        # 澶勭悊鎺у埗鎸囦护
        if topic == "edge/control/start":
            self.start_detection()
        elif topic == "edge/control/stop":
            self.stop_detection()
        elif topic == "edge/control/config":
            self.update_config(payload)

    def on_publish(self, client, userdata, mid):
        """鍙戝竷娑堟伅鍥炶皟"""
        print(f"馃摛 娑堟伅鍙戝竷鎴愬姛锛屾秷鎭疘D: {mid}")

    def encode_image_to_base64(self, frame):
        """灏哋penCV甯х紪鐮佷负Base64瀛楃涓?""
        try:
            # 灏嗗抚缂栫爜涓篔PEG鏍煎紡
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            # 杞崲涓築ase64
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            return image_base64
        except Exception as e:
            print(f"鉁?鍥剧墖缂栫爜澶辫触: {e}")
            return None

    def send_detection_result(self, result_data, frame=None):
        """鍙戦€佹娴嬬粨鏋滃埌鍚庣锛堝寘鍚浘鐗囷級"""
        topic = "edge/detection/results"

        # 鏋勫缓鍚庣鏈熸湜鐨勬秷鎭牸寮?        message = {
            "device_id": result_data.get("device_id", self.client_id),
            "timestamp": result_data.get("timestamp", int(time.time())),
            "detections": result_data.get("detections", [])
        }

        # 濡傛灉鏈夊抚锛屾坊鍔燘ase64鍥剧墖
        if frame is not None:
            image_base64 = self.encode_image_to_base64(frame)
            if image_base64:
                message["image"] = image_base64
                print(f"馃摳 鍥剧墖宸茬紪鐮侊紝澶у皬: {len(image_base64)} 瀛楃")

        payload = json.dumps(message, ensure_ascii=False)

        try:
            self.client.publish(topic, payload, qos=1)
            print(f"馃摛 妫€娴嬬粨鏋滃凡鍙戦€佸埌 {topic}")
            print(f"   鍖呭惈 {len(message['detections'])} 涓娴嬬粨鏋?)
            if "image" in message:
                print(f"   鍖呭惈鍥剧墖鏁版嵁")
        except Exception as e:
            print(f"鉁?鍙戦€佹娴嬬粨鏋滃け璐? {e}")

    def send_alert(self, alert_data, frame=None):
        """鍙戦€佸憡璀︿俊鎭紙鍖呭惈鍥剧墖锛?""
        topic = "edge/alerts/urgent"

        # 鏋勫缓鍚庣鏈熸湜鐨勫憡璀︽秷鎭牸寮?        message = {
            "device_id": alert_data.get("device_id", self.client_id),
            "timestamp": alert_data.get("timestamp", int(time.time())),
            "type": alert_data.get("alert_type", "ALERT"),
            "severity": "HIGH",
            "description": alert_data.get("class", "妫€娴嬪埌寮傚父")
        }

        # 濡傛灉鏈夊抚锛屾坊鍔燘ase64鍥剧墖
        if frame is not None:
            image_base64 = self.encode_image_to_base64(frame)
            if image_base64:
                message["image"] = image_base64

        payload = json.dumps(message, ensure_ascii=False)

        try:
            self.client.publish(topic, payload, qos=2)
            print(f"馃毃 鍛婅宸插彂閫佸埌 {topic}")
        except Exception as e:
            print(f"鉁?鍙戦€佸憡璀﹀け璐? {e}")

    def send_heartbeat(self):
        """鍙戦€佸績璺冲寘"""
        topic = "edge/heartbeat"
        payload = json.dumps({
            "device_id": self.client_id,
            "timestamp": int(time.time()),
            "status": "online"
        })

        try:
            self.client.publish(topic, payload, qos=0)
        except Exception as e:
            print(f"鉁?鍙戦€佸績璺冲け璐? {e}")

    def process_frame(self, frame):
        """澶勭悊鍗曞抚鍥惧儚"""
        try:
            # YOLOv8鎺ㄧ悊
            results = self.model(frame)

            detection_data = {
                "timestamp": int(time.time()),
                "device_id": self.client_id,
                "model": self.model_path,
                "detections": []
            }

            # 瑙ｆ瀽妫€娴嬬粨鏋?            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # 鑾峰彇妫€娴嬫淇℃伅
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]

                    detection = {
                        "class": class_name,
                        "confidence": round(confidence, 3),
                        "bbox": {
                            "x1": round(x1, 2),
                            "y1": round(y1, 2),
                            "x2": round(x2, 2),
                            "y2": round(y2, 2)
                        }
                    }

                    detection_data["detections"].append(detection)

            return detection_data

        except Exception as e:
            print(f"鉁?澶勭悊甯ф椂鍑洪敊: {e}")
            return None

    def start_detection(self):
        """鍚姩妫€娴?""
        if self.is_running:
            print("鈿?妫€娴嬪凡鍦ㄨ繍琛屼腑")
            return

        self.is_running = True
        print("馃殌 鍚姩鐩爣妫€娴?..")

        # 鎵撳紑鎽勫儚澶?        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("鉁?鏃犳硶鎵撳紑鎽勫儚澶?)
            self.is_running = False
            return

        frame_count = 0
        detection_interval = 10  # 姣?0甯у彂閫佷竴娆＄粨鏋?        heartbeat_interval = 30  # 姣?0甯у彂閫佷竴娆″績璺?
        try:
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    print("鈿?鏃犳硶璇诲彇甯э紝閲嶆柊灏濊瘯...")
                    cap.release()
                    cap = cv2.VideoCapture(0)
                    time.sleep(1)
                    continue

                # 澶勭悊甯?                detection_data = self.process_frame(frame)

                if detection_data and detection_data["detections"]:
                    # 瀹氭湡鍙戦€佹娴嬬粨鏋?                    frame_count += 1
                    if frame_count % detection_interval == 0:
                        self.send_detection_result(detection_data, frame)

                    # 瀹氭湡鍙戦€佸績璺?                    if frame_count % heartbeat_interval == 0:
                        self.send_heartbeat()

                    # 妫€鏌ユ槸鍚︽娴嬪埌鐗瑰畾鐩爣锛堥珮缃俊搴﹀憡璀︼級
                    for detection in detection_data["detections"]:
                        if detection["confidence"] > 0.8:
                            # 鍙戦€侀珮缃俊搴﹀憡璀?                            alert_data = {
                                "timestamp": detection_data["timestamp"],
                                "device_id": self.client_id,
                                "alert_type": "high_confidence_detection",
                                "class": detection["class"],
                                "confidence": detection["confidence"],
                                "location": detection["bbox"]
                            }
                            self.send_alert(alert_data, frame)

                # 鎺у埗甯х巼
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n鈿?妫€娴嬭鐢ㄦ埛涓柇")
        except Exception as e:
            print(f"鉁?妫€娴嬭繃绋嬩腑鍑洪敊: {e}")
        finally:
            cap.release()
            self.is_running = False
            print("馃洃 妫€娴嬪凡鍋滄")

    def stop_detection(self):
        """鍋滄妫€娴?""
        if not self.is_running:
            print("鈿?妫€娴嬫湭鍦ㄨ繍琛?)
            return

        self.is_running = False
        print("馃洃 姝ｅ湪鍋滄鐩爣妫€娴?..")

    def update_config(self, config_json):
        """鏇存柊閰嶇疆"""
        try:
            config = json.loads(config_json)
            print(f"馃摑 鏇存柊閰嶇疆: {config}")
            # 杩欓噷鍙互娣诲姞閰嶇疆鏇存柊閫昏緫
        except Exception as e:
            print(f"鉁?閰嶇疆鏇存柊澶辫触: {e}")

    def disconnect(self):
        """鏂紑杩炴帴"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print("鉁?MQTT杩炴帴宸叉柇寮€")

# 涓荤▼搴?if __name__ == "__main__":
    print("=" * 50)
    print("杈圭紭璁＄畻瀹㈡埛绔惎鍔?)
    print("=" * 50)

    # 鍒涘缓杈圭紭璁＄畻瀹㈡埛绔?    edge_client = EdgeComputingClient(
        broker_url='localhost',
        broker_port=1883,
        client_id='edge-camera-001'
    )

    # 绛夊緟杩炴帴寤虹珛
    print("鈴?绛夊緟MQTT杩炴帴寤虹珛...")
    time.sleep(3)

    try:
        print("\n馃挕 鎻愮ず: 绛夊緟鎺у埗鎸囦护鎴栨寜 Ctrl+C 閫€鍑?)
        print("馃挕 鍙敤鐨勬帶鍒舵寚浠?")
        print("   - edge/control/start: 鍚姩妫€娴?)
        print("   - edge/control/stop: 鍋滄妫€娴?)
        print("   - edge/control/config: 鏇存柊閰嶇疆")
        print()

        # 淇濇寔杩愯锛岀瓑寰呮帶鍒舵寚浠?        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n馃憢 绋嬪簭琚敤鎴蜂腑鏂?)
    finally:
        edge_client.disconnect()
        print("馃憢 绋嬪簭宸查€€鍑?)
