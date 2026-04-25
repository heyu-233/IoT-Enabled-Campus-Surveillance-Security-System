package com.example.end_part.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class Camera {
    private Long id;
    private String name;
    private String deviceId;
    private String ipAddress;
    private Integer port;
    private String location;
    private String status;
    private String streamUrl;
    private LocalDateTime lastActive;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
