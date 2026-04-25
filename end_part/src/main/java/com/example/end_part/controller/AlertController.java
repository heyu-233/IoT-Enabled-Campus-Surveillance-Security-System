package com.example.end_part.controller;

import com.example.end_part.dto.AlertProcessRequest;
import com.example.end_part.dto.PagedResponse;
import com.example.end_part.entity.Alert;
import com.example.end_part.service.AlertService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/alerts")
public class AlertController {

    @Autowired
    private AlertService alertService;

    @GetMapping
    public ResponseEntity<PagedResponse<Alert>> getList(@RequestParam Map<String, Object> params) {
        return new ResponseEntity<>(alertService.getList(params), HttpStatus.OK);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Alert> getById(@PathVariable Long id) {
        return new ResponseEntity<>(alertService.getById(id), HttpStatus.OK);
    }

    @PostMapping("/{id}/process")
    public ResponseEntity<Alert> markAsProcessed(@PathVariable Long id, @RequestBody AlertProcessRequest data) {
        return new ResponseEntity<>(alertService.markAsProcessed(id, data), HttpStatus.OK);
    }

    @GetMapping("/search")
    public ResponseEntity<PagedResponse<Alert>> search(@RequestParam Map<String, Object> params) {
        return new ResponseEntity<>(alertService.search(params), HttpStatus.OK);
    }

    @PostMapping
    public ResponseEntity<Alert> createAlert(@RequestBody Alert alert) {
        return new ResponseEntity<>(alertService.createAlert(alert), HttpStatus.CREATED);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteAlert(@PathVariable Long id) {
        alertService.delete(id);
        return new ResponseEntity<>(HttpStatus.NO_CONTENT);
    }
}
