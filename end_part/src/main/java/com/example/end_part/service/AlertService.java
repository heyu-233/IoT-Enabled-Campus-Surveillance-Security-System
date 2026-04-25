package com.example.end_part.service;

import com.example.end_part.dto.AlertProcessRequest;
import com.example.end_part.dto.PagedResponse;
import com.example.end_part.entity.Alert;
import com.example.end_part.mapper.AlertMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AlertService {

    @Autowired
    private AlertMapper alertMapper;

    public PagedResponse<Alert> getList(Map<String, Object> params) {
        int page = parsePositiveInt(params.get("page"), 1);
        int pageSize = parsePositiveInt(params.get("pageSize"), 20);
        int offset = (page - 1) * pageSize;
        List<Alert> alerts = alertMapper.findPage(pageSize, offset);
        long total = alertMapper.countAll();
        return new PagedResponse<>(alerts, total, page, pageSize);
    }

    public Alert getById(Long id) {
        Alert alert = alertMapper.findById(id);
        if (alert == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Alert not found");
        }
        return alert;
    }

    public Alert markAsProcessed(Long id, AlertProcessRequest data) {
        Alert alert = getById(id);
        if (data == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Missing alert process payload");
        }
        String nextStatus = normalizeStatus(data.getStatus(), alert.getStatus());
        String processedBy = data.getProcessedBy() == null ? "" : data.getProcessedBy().trim();
        if (!"UNPROCESSED".equals(nextStatus) && processedBy.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "processedBy is required when updating alert handling");
        }

        alert.setStatus(nextStatus);
        alert.setProcessedBy(processedBy.isBlank() ? null : processedBy);
        alert.setProcessingNotes(data.getProcessingNotes());
        if ("PROCESSED".equals(nextStatus)) {
            alert.setProcessedAt(LocalDateTime.now());
        } else if ("PROCESSING".equals(nextStatus)) {
            alert.setProcessedAt(null);
        } else {
            alert.setProcessedAt(null);
            alert.setProcessedBy(null);
        }
        alertMapper.updateStatus(alert);
        return alertMapper.findById(id);
    }

    public PagedResponse<Alert> search(Map<String, Object> params) {
        int page = parsePositiveInt(params.get("page"), 1);
        int pageSize = parsePositiveInt(params.get("pageSize"), 20);
        int offset = (page - 1) * pageSize;
        Map<String, Object> query = new HashMap<>(params);
        query.put("limit", pageSize);
        query.put("offset", offset);
        List<Alert> alerts = alertMapper.search(query);
        long total = alertMapper.searchCount(query);
        return new PagedResponse<>(alerts, total, page, pageSize);
    }

    public Alert createAlert(Alert alert) {
        alert.setStatus("UNPROCESSED");
        alert.setCreatedAt(LocalDateTime.now());
        alertMapper.insert(alert);
        return alertMapper.findById(alert.getId());
    }

    public void delete(Long id) {
        getById(id);
        alertMapper.delete(id);
    }

    private int parsePositiveInt(Object raw, int fallback) {
        if (raw == null) {
            return fallback;
        }
        try {
            int value = Integer.parseInt(raw.toString());
            return value > 0 ? value : fallback;
        } catch (NumberFormatException ex) {
            return fallback;
        }
    }

    private String normalizeStatus(String requestedStatus, String currentStatus) {
        if (requestedStatus == null || requestedStatus.isBlank()) {
            return currentStatus == null ? "PROCESSED" : currentStatus;
        }
        return switch (requestedStatus.toUpperCase()) {
            case "UNPROCESSED", "PROCESSING", "PROCESSED" -> requestedStatus.toUpperCase();
            default -> throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unsupported alert status");
        };
    }
}
