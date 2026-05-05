package com.example.end_part.controller;

import com.example.end_part.service.DetectionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class DetectionController {

    @Autowired
    private DetectionService detectionService;

    @PostMapping("/detections")
    public ResponseEntity<Map<String, Object>> receiveDetection(@RequestBody String payload) {
        detectionService.processDetection(payload);
        return ResponseEntity.ok(Map.of("status", "ok"));
    }
}
