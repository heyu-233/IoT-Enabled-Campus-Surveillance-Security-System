package com.example.end_part.controller;

import com.example.end_part.service.AnalyticsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/analytics")
public class AnalyticsController {

    @Autowired
    private AnalyticsService analyticsService;

    @GetMapping("/type-distribution")
    public ResponseEntity<Map<String, Object>> getTypeDistribution(@RequestParam Map<String, Object> params) {
        Map<String, Object> result = analyticsService.getTypeDistribution(params);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

    @GetMapping("/daily-alerts")
    public ResponseEntity<Map<String, Object>> getDailyAlerts(@RequestParam Map<String, Object> params) {
        Map<String, Object> result = analyticsService.getDailyAlerts(params);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

    @GetMapping("/area-heatmap")
    public ResponseEntity<Map<String, Object>> getAreaHeatmap(@RequestParam Map<String, Object> params) {
        Map<String, Object> result = analyticsService.getAreaHeatmap(params);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

    @GetMapping("/types/{type}")
    public ResponseEntity<Map<String, Object>> getTypeDetails(@PathVariable String type, @RequestParam Map<String, Object> params) {
        Map<String, Object> result = analyticsService.getTypeDetails(type, params);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }
}
