package com.example.end_part.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AlertSetting {
    private Long id;
    private Boolean emailNotifications;
    private Boolean smsNotifications;
    private Boolean pushNotifications;
    private String emailRecipients;
    private String smsRecipients;
    private String severityLevels;
    private LocalDateTime updatedAt;
}
