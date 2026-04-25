CREATE DATABASE IF NOT EXISTS qgg_backend DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE qgg_backend;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'USER',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS cameras (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    device_id VARCHAR(100) NOT NULL UNIQUE,
    ip_address VARCHAR(50) NOT NULL,
    port INT NOT NULL,
    location VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OFFLINE',
    stream_url VARCHAR(200) NOT NULL,
    last_active DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS behaviors (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    camera_id BIGINT NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    image_url VARCHAR(200),
    original_image_url VARCHAR(200),
    confidence DOUBLE NOT NULL DEFAULT 0.0,
    occurred_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_behaviors_camera_id (camera_id),
    INDEX idx_behaviors_type (type),
    INDEX idx_behaviors_occurred_at (occurred_at),
    FOREIGN KEY (camera_id) REFERENCES cameras(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    behavior_id BIGINT NOT NULL,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'UNPROCESSED',
    description TEXT NOT NULL,
    processed_by VARCHAR(50),
    processing_notes TEXT,
    processed_at DATETIME,
    created_at DATETIME NOT NULL,
    INDEX idx_alerts_behavior_id (behavior_id),
    INDEX idx_alerts_status (status),
    INDEX idx_alerts_type (type),
    INDEX idx_alerts_created_at (created_at),
    FOREIGN KEY (behavior_id) REFERENCES behaviors(id)
);

CREATE TABLE IF NOT EXISTS alert_settings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email_notifications BOOLEAN NOT NULL DEFAULT FALSE,
    sms_notifications BOOLEAN NOT NULL DEFAULT FALSE,
    push_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    email_recipients TEXT,
    sms_recipients TEXT,
    severity_levels VARCHAR(100) NOT NULL DEFAULT 'HIGH,MEDIUM',
    updated_at DATETIME NOT NULL
);

ALTER TABLE cameras ADD COLUMN IF NOT EXISTS device_id VARCHAR(100) NULL UNIQUE AFTER name;
ALTER TABLE behaviors ADD COLUMN IF NOT EXISTS original_image_url VARCHAR(200) NULL AFTER image_url;

INSERT IGNORE INTO cameras (name, device_id, ip_address, port, location, status, stream_url, last_active, created_at, updated_at) VALUES
('Camera 1', 'edge-camera-01', '192.0.2.10', 554, 'Main Entrance', 'ONLINE', 'http://127.0.0.1:8080/live/camera1.flv', NOW(), NOW(), NOW()),
('Camera 2', 'edge-camera-02', '192.0.2.11', 554, 'Back Entrance', 'ONLINE', 'http://127.0.0.1:8080/live/camera2.flv', NOW(), NOW(), NOW()),
('Camera 3', 'edge-camera-03', '192.0.2.12', 554, 'Parking Lot', 'OFFLINE', 'http://127.0.0.1:8080/live/camera3.flv', NOW(), NOW(), NOW());

INSERT IGNORE INTO alert_settings (email_notifications, sms_notifications, push_notifications, email_recipients, sms_recipients, severity_levels, updated_at) VALUES
(FALSE, FALSE, TRUE, '', '', 'HIGH,MEDIUM', NOW());

INSERT IGNORE INTO behaviors (camera_id, type, description, image_url, original_image_url, confidence, occurred_at, created_at) VALUES
(1, 'intrusion', 'Suspicious intrusion detected', '/images/demo_intrusion_processed.jpg', '/images/demo_intrusion_original.jpg', 0.90, NOW() - INTERVAL 1 HOUR, NOW() - INTERVAL 1 HOUR),
(2, 'loitering', 'Person is loitering near gate', '/images/demo_loitering_processed.jpg', '/images/demo_loitering_original.jpg', 0.80, NOW() - INTERVAL 2 HOUR, NOW() - INTERVAL 2 HOUR),
(3, 'left_object', 'Object left unattended', NULL, NULL, 0.70, NOW() - INTERVAL 3 HOUR, NOW() - INTERVAL 3 HOUR);

INSERT IGNORE INTO alerts (behavior_id, type, severity, status, description, created_at) VALUES
(1, 'intrusion', 'LOW', 'UNPROCESSED', 'Suspicious intrusion detected', NOW() - INTERVAL 1 HOUR),
(2, 'loitering', 'MEDIUM', 'PROCESSING', 'Person is loitering near gate', NOW() - INTERVAL 2 HOUR),
(3, 'left_object', 'HIGH', 'PROCESSED', 'Object left unattended', NOW() - INTERVAL 3 HOUR);
