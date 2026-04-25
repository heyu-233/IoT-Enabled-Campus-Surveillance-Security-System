package com.example.end_part.service;

import com.example.end_part.entity.AlertSetting;
import com.example.end_part.mapper.AlertSettingMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class ConfigService {

    @Autowired
    private AlertSettingMapper alertSettingMapper;

    public AlertSetting getAlertSettings() {
        AlertSetting alertSetting = alertSettingMapper.findOne();
        if (alertSetting == null) {
            // 如果没有设置，创建默认设置
            alertSetting = new AlertSetting();
            alertSetting.setEmailNotifications(false);
            alertSetting.setSmsNotifications(false);
            alertSetting.setPushNotifications(true);
            alertSetting.setEmailRecipients("");
            alertSetting.setSmsRecipients("");
            alertSetting.setSeverityLevels("HIGH,MEDIUM");
            alertSetting.setUpdatedAt(LocalDateTime.now());
            alertSettingMapper.insert(alertSetting);
        }
        return alertSetting;
    }

    public AlertSetting updateAlertSettings(AlertSetting alertSetting) {
        AlertSetting existingSetting = alertSettingMapper.findOne();
        if (existingSetting == null) {
            alertSetting.setUpdatedAt(LocalDateTime.now());
            alertSettingMapper.insert(alertSetting);
        } else {
            existingSetting.setEmailNotifications(alertSetting.getEmailNotifications());
            existingSetting.setSmsNotifications(alertSetting.getSmsNotifications());
            existingSetting.setPushNotifications(alertSetting.getPushNotifications());
            existingSetting.setEmailRecipients(alertSetting.getEmailRecipients());
            existingSetting.setSmsRecipients(alertSetting.getSmsRecipients());
            existingSetting.setSeverityLevels(alertSetting.getSeverityLevels());
            existingSetting.setUpdatedAt(LocalDateTime.now());
            alertSettingMapper.update(existingSetting);
            alertSetting = existingSetting;
        }
        return alertSetting;
    }
}
