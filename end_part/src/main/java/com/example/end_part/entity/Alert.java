package com.example.end_part.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class Alert {
    private Long id;
    private Long behaviorId;
    private String type;
    private String severity;
    private String status;
    private String description;
    private String processedBy;
    private String processingNotes;
    private LocalDateTime processedAt;
    private LocalDateTime createdAt;
    private String screenshot;
    private String originalImageUrl;
    private String processedImageUrl;
    private Double confidence;
    private LocalDateTime behaviorOccurredAt;
    private Long cameraId;
    private String cameraName;
    private String cameraLocation;
}
