package com.example.end_part.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class Behavior {
    private Long id;
    private Long cameraId;
    private String type;
    private String description;
    private String imageUrl;
    private String originalImageUrl;
    private String processedImageUrl;
    private Double confidence;
    private LocalDateTime occurredAt;
    private LocalDateTime createdAt;
}
