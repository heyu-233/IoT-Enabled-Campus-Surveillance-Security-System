package com.example.end_part.controller;

import com.example.end_part.entity.AlertSetting;
import com.example.end_part.service.ConfigService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/config")
public class ConfigController {

    @Autowired
    private ConfigService configService;

    @GetMapping("/alert-settings")
    public ResponseEntity<AlertSetting> getAlertSettings() {
        AlertSetting alertSetting = configService.getAlertSettings();
        return new ResponseEntity<>(alertSetting, HttpStatus.OK);
    }

    @PutMapping("/alert-settings")
    public ResponseEntity<AlertSetting> updateAlertSettings(@RequestBody AlertSetting alertSetting) {
        AlertSetting updatedSetting = configService.updateAlertSettings(alertSetting);
        return new ResponseEntity<>(updatedSetting, HttpStatus.OK);
    }
}
