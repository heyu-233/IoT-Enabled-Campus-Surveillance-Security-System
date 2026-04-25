package com.example.end_part.dto;

import lombok.Data;

@Data
public class AlertProcessRequest {
    private String processedBy;
    private String processingNotes;
    private String status;
}
