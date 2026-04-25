package com.example.end_part.service;

import com.example.end_part.mapper.AlertMapper;
import com.example.end_part.mapper.BehaviorMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AnalyticsService {

    @Autowired
    private AlertMapper alertMapper;

    @Autowired
    private BehaviorMapper behaviorMapper;

    public Map<String, Object> getTypeDistribution(Map<String, Object> params) {
        return Map.of("items", alertMapper.countDistribution());
    }

    public Map<String, Object> getDailyAlerts(Map<String, Object> params) {
        List<Map<String, Object>> rows = alertMapper.countDaily();
        return Map.of(
                "labels", rows.stream().map(row -> String.valueOf(row.get("label"))).toList(),
                "values", rows.stream().map(row -> ((Number) row.get("value")).longValue()).toList()
        );
    }

    public Map<String, Object> getAreaHeatmap(Map<String, Object> params) {
        return Map.of("items", alertMapper.countByArea());
    }

    public Map<String, Object> getTypeDetails(String type, Map<String, Object> params) {
        long totalAlerts = alertMapper.countByType(type);
        long processedAlerts = alertMapper.countProcessedByType(type);
        Double averageConfidence = behaviorMapper.averageConfidenceByType(type);
        List<Map<String, Object>> rows = alertMapper.countTimelineByType(type);

        Map<String, Object> summary = new HashMap<>();
        summary.put("type", type);
        summary.put("totalAlerts", totalAlerts);
        summary.put("processedAlerts", processedAlerts);
        summary.put("averageConfidence", averageConfidence == null ? 0.0 : averageConfidence);

        return Map.of(
                "summary", summary,
                "labels", rows.stream().map(row -> String.valueOf(row.get("label"))).toList(),
                "values", rows.stream().map(row -> ((Number) row.get("value")).longValue()).toList()
        );
    }
}
