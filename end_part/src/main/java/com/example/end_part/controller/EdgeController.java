package com.example.end_part.controller;

import com.example.end_part.config.MqttConfig;
import com.example.end_part.dto.EdgeCommandResponse;
import com.example.end_part.service.DetectorSupervisorClient;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;

@RestController
@RequestMapping
public class EdgeController {

    @Autowired
    private MqttConfig.MqttPublisher mqttPublisher;

    @Autowired
    private DetectorSupervisorClient detectorSupervisorClient;

    @PostMapping("/edge/stream/start")
    public ResponseEntity<EdgeCommandResponse> startStream(@RequestParam String deviceId) {
        return publish("edge/stream/start", buildCommandPayload("start_stream", deviceId));
    }

    @PostMapping("/edge/stream/stop")
    public ResponseEntity<EdgeCommandResponse> stopStream(@RequestParam String deviceId) {
        return publish("edge/stream/stop", buildCommandPayload("stop_stream", deviceId));
    }

    @PostMapping("/host/detector/start")
    public ResponseEntity<EdgeCommandResponse> startDetector(@RequestParam String deviceId) {
        return ResponseEntity.ok(detectorSupervisorClient.start(deviceId));
    }

    @PostMapping("/host/detector/stop")
    public ResponseEntity<EdgeCommandResponse> stopDetector(@RequestParam String deviceId) {
        return ResponseEntity.ok(detectorSupervisorClient.stop(deviceId));
    }

    @PostMapping("/host/detector/config")
    public ResponseEntity<EdgeCommandResponse> updateDetectorConfig(@RequestParam String deviceId, @RequestBody(required = false) String config) {
        return ResponseEntity.ok(detectorSupervisorClient.config(deviceId, config));
    }

    @PostMapping("/host/detector/status")
    public ResponseEntity<EdgeCommandResponse> detectorStatus() {
        return ResponseEntity.ok(detectorSupervisorClient.status());
    }

    @PostMapping("/edge/buzzer/on")
    public ResponseEntity<EdgeCommandResponse> buzzerOn(@RequestParam String deviceId) {
        return publish("edge/buzzer/on", buildCommandPayload("buzzer_on", deviceId));
    }

    @PostMapping("/edge/buzzer/off")
    public ResponseEntity<EdgeCommandResponse> buzzerOff(@RequestParam String deviceId) {
        return publish("edge/buzzer/off", buildCommandPayload("buzzer_off", deviceId));
    }

    @PostMapping("/edge/led/blink")
    public ResponseEntity<EdgeCommandResponse> ledBlink(@RequestParam String deviceId) {
        return publish("edge/led/blink", buildCommandPayload("led_blink", deviceId));
    }

    @PostMapping("/edge/control/start")
    public ResponseEntity<EdgeCommandResponse> legacyStartDetection(@RequestParam String deviceId) {
        return startDetector(deviceId);
    }

    @PostMapping("/edge/control/stop")
    public ResponseEntity<EdgeCommandResponse> legacyStopDetection(@RequestParam String deviceId) {
        return stopDetector(deviceId);
    }

    @PostMapping("/edge/control/config")
    public ResponseEntity<EdgeCommandResponse> legacyUpdateConfig(@RequestParam String deviceId, @RequestBody(required = false) String config) {
        return updateDetectorConfig(deviceId, config);
    }

    @PostMapping("/edge/control/buzzer")
    public ResponseEntity<EdgeCommandResponse> legacyTriggerBuzzer(@RequestParam String deviceId) {
        return buzzerOn(deviceId);
    }

    private String buildCommandPayload(String command, String deviceId) {
        return String.format("{\"command\":\"%s\",\"device_id\":\"%s\"}", command, deviceId);
    }

    private ResponseEntity<EdgeCommandResponse> publish(String topic, String payload) {
        try {
            mqttPublisher.publish(topic, payload);
            return ResponseEntity.ok(new EdgeCommandResponse(true, "Command published to " + topic, LocalDateTime.now()));
        } catch (MqttException e) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                    .body(new EdgeCommandResponse(false, e.getMessage(), LocalDateTime.now()));
        }
    }
}
