package com.example.end_part.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
public class EdgeCommandResponse {
    private boolean success;
    private String message;
    private LocalDateTime timestamp;
}
