package com.example.end_part.service;

import com.example.end_part.config.MqttConfig;
import com.example.end_part.entity.Alert;
import com.example.end_part.entity.Behavior;
import com.example.end_part.entity.Camera;
import com.example.end_part.mapper.AlertMapper;
import com.example.end_part.mapper.BehaviorMapper;
import com.example.end_part.mapper.CameraMapper;
import com.example.end_part.utils.ImageUtils;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.List;
import java.util.Map;
import java.util.Objects;

@Service
public class MqttMessageService {

    private static final Logger logger = LoggerFactory.getLogger(MqttMessageService.class);

    @Autowired
    private BehaviorMapper behaviorMapper;

    @Autowired
    private AlertMapper alertMapper;

    @Autowired
    private CameraMapper cameraMapper;

    @Autowired
    private ImageUtils imageUtils;

    @Autowired
    @Lazy
    private MqttConfig.MqttPublisher mqttPublisher;

    @Value("${mqtt.topic.buzzer:edge/control/buzzer}")
    private String buzzerTopic;

    @Value("${alert.auto.threshold:0.8}")
    private double alertThreshold;

    private final ObjectMapper objectMapper = new ObjectMapper();

    public void handleMessage(String topic, String payload) {
        logger.info("Received MQTT message on topic {}", topic);
        try {
            if (topic.startsWith("edge/detection/")) {
                handleDetectionResult(payload);
            } else if (topic.startsWith("edge/alerts/")) {
                handleEdgeAlert(payload);
            } else if (topic.startsWith("sensors/")) {
                handleSensorData(topic, payload);
            } else if (topic.startsWith("alerts/")) {
                handleAlertData(topic, payload);
            } else if (topic.equals("edge/heartbeat")) {
                handleHeartbeat(payload);
            } else {
                logger.warn("Unhandled MQTT topic pattern: {}", topic);
            }
        } catch (Exception e) {
            logger.error("Failed to process MQTT payload on topic {}", topic, e);
        }
    }

    private void handleDetectionResult(String payload) {
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> data = objectMapper.readValue(payload, Map.class);
            String deviceId = (String) data.get("device_id");
            Long timestamp = extractTimestamp(data);
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> detections = (List<Map<String, Object>>) data.get("detections");

            Camera camera = resolveCamera(deviceId);
            if (camera == null) {
                logger.warn("Skipping detection result because device_id {} is not bound to a camera", deviceId);
                return;
            }

            markCameraOnline(camera);
            SavedImages savedImages = saveImages(data, "detection");

            if (detections == null || detections.isEmpty()) {
                logger.info("Detection payload for device {} contained no detections", deviceId);
                return;
            }

            for (Map<String, Object> detection : detections) {
                Object confidenceValue = detection.get("confidence");
                if (!(confidenceValue instanceof Number confidenceNumber)) {
                    logger.warn("Skipping malformed detection without confidence: {}", detection);
                    continue;
                }

                String className = String.valueOf(detection.getOrDefault("class", "unknown"));
                Double confidence = confidenceNumber.doubleValue();

                Behavior behavior = new Behavior();
                behavior.setCameraId(camera.getId());
                behavior.setType(className);
                behavior.setDescription("Detected: " + className);
                behavior.setImageUrl(savedImages.processedImageUrl());
                behavior.setProcessedImageUrl(savedImages.processedImageUrl());
                behavior.setOriginalImageUrl(savedImages.originalImageUrl());
                behavior.setConfidence(confidence);
                behavior.setOccurredAt(toOccurredAt(timestamp));
                behavior.setCreatedAt(LocalDateTime.now());
                behaviorMapper.insert(behavior);

                if (confidence >= alertThreshold) {
                    createAlertFromBehavior(behavior, className, confidence);
                }
            }
        } catch (Exception e) {
            logger.error("Failed to handle detection result payload", e);
        }
    }

    private void handleEdgeAlert(String payload) {
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> alertData = objectMapper.readValue(payload, Map.class);
            String deviceId = (String) alertData.get("device_id");
            String alertType = (String) alertData.get("type");
            String severity = (String) alertData.get("severity");
            String description = (String) alertData.get("description");
            Long timestamp = extractTimestamp(alertData);

            Camera camera = resolveCamera(deviceId);
            if (camera == null) {
                logger.warn("Skipping edge alert because device_id {} is not bound to a camera", deviceId);
                return;
            }

            markCameraOnline(camera);
            SavedImages savedImages = saveImages(alertData, "alert");

            Behavior behavior = new Behavior();
            behavior.setCameraId(camera.getId());
            behavior.setType(alertType != null ? alertType : "ALERT");
            behavior.setDescription(description != null ? description : "Edge device alert");
            behavior.setImageUrl(savedImages.processedImageUrl());
            behavior.setProcessedImageUrl(savedImages.processedImageUrl());
            behavior.setOriginalImageUrl(savedImages.originalImageUrl());
            behavior.setConfidence(1.0);
            behavior.setOccurredAt(toOccurredAt(timestamp));
            behavior.setCreatedAt(LocalDateTime.now());
            behaviorMapper.insert(behavior);

            Alert alert = new Alert();
            alert.setBehaviorId(behavior.getId());
            alert.setType(alertType != null ? alertType : "EDGE_ALERT");
            alert.setSeverity(severity != null ? severity.toUpperCase() : "HIGH");
            alert.setStatus("UNPROCESSED");
            alert.setDescription(description != null ? description : "Alert raised by edge device");
            alert.setCreatedAt(LocalDateTime.now());
            alertMapper.insert(alert);
            publishBuzzerSignal();
        } catch (Exception e) {
            logger.error("Failed to handle edge alert payload", e);
        }
    }

    private void createAlertFromBehavior(Behavior behavior, String className, Double confidence) {
        Alert alert = new Alert();
        alert.setBehaviorId(behavior.getId());
        alert.setType(className);
        if (confidence >= 0.95) {
            alert.setSeverity("HIGH");
        } else if (confidence >= 0.85) {
            alert.setSeverity("MEDIUM");
        } else {
            alert.setSeverity("LOW");
        }
        alert.setStatus("UNPROCESSED");
        alert.setDescription("Auto alert: detected " + className + " with confidence " + String.format("%.2f", confidence));
        alert.setCreatedAt(LocalDateTime.now());
        alertMapper.insert(alert);
        publishBuzzerSignal();
    }

    private Camera resolveCamera(String deviceId) {
        if (deviceId == null || deviceId.isBlank()) {
            logger.warn("MQTT payload is missing device_id");
            return null;
        }
        return cameraMapper.findByDeviceId(deviceId);
    }

    private void markCameraOnline(Camera camera) {
        camera.setStatus("ONLINE");
        camera.setLastActive(LocalDateTime.now());
        camera.setUpdatedAt(LocalDateTime.now());
        cameraMapper.updateStatus(camera);
    }

    private SavedImages saveImages(Map<String, Object> data, String prefix) {
        String originalBase64 = firstNonBlank(data.get("original_image"), data.get("raw_image"), data.get("source_image"));
        String processedBase64 = firstNonBlank(data.get("processed_image"), data.get("result_image"), data.get("annotated_image"), data.get("image"));

        if (originalBase64 == null && processedBase64 == null) {
            logger.info("No image payload found for {} message", prefix);
            return new SavedImages(null, null);
        }

        if (originalBase64 == null) {
            originalBase64 = processedBase64;
        }
        if (processedBase64 == null) {
            processedBase64 = originalBase64;
        }

        String originalImageUrl = imageUtils.saveBase64Image(originalBase64, prefix + "_original");
        String processedImageUrl = Objects.equals(originalBase64, processedBase64)
                ? originalImageUrl
                : imageUtils.saveBase64Image(processedBase64, prefix + "_processed");

        if (originalImageUrl == null && processedImageUrl == null) {
            logger.warn("Image payload was present but no file could be persisted for {}", prefix);
        }
        return new SavedImages(originalImageUrl, processedImageUrl);
    }

    private String firstNonBlank(Object... candidates) {
        for (Object candidate : candidates) {
            if (candidate instanceof String value && !value.isBlank()) {
                return value;
            }
        }
        return null;
    }

    private Long extractTimestamp(Map<String, Object> data) {
        if (data.get("timestamp") instanceof Number number) {
            return number.longValue();
        }
        return null;
    }

    private LocalDateTime toOccurredAt(Long timestamp) {
        if (timestamp == null) {
            return LocalDateTime.now();
        }
        return LocalDateTime.ofInstant(Instant.ofEpochSecond(timestamp), ZoneId.systemDefault());
    }

    private void publishBuzzerSignal() {
        try {
            mqttPublisher.publish(buzzerTopic, "buzz");
        } catch (Exception e) {
            logger.warn("Failed to publish buzzer command", e);
        }
    }

    private void handleSensorData(String topic, String payload) {
        logger.info("Sensor topic {} payload {}", topic, payload);
    }

    private void handleAlertData(String topic, String payload) {
        logger.info("Alert topic {} payload {}", topic, payload);
    }

    private void handleHeartbeat(String payload) {
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> heartbeatData = objectMapper.readValue(payload, Map.class);
            String deviceId = (String) heartbeatData.get("device_id");
            String status = (String) heartbeatData.get("status");
            Camera camera = resolveCamera(deviceId);
            if (camera != null) {
                camera.setStatus("ONLINE".equalsIgnoreCase(status) ? "ONLINE" : "OFFLINE");
                camera.setLastActive(LocalDateTime.now());
                camera.setUpdatedAt(LocalDateTime.now());
                cameraMapper.updateStatus(camera);
            }
        } catch (Exception e) {
            logger.error("Failed to handle heartbeat payload", e);
        }
    }

    private record SavedImages(String originalImageUrl, String processedImageUrl) {
    }
}
