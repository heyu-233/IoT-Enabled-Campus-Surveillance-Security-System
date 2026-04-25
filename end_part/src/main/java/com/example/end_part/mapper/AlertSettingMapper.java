package com.example.end_part.mapper;

import com.example.end_part.entity.AlertSetting;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Update;

@Mapper
public interface AlertSettingMapper {
    @Select("SELECT * FROM alert_settings LIMIT 1")
    AlertSetting findOne();

    @Insert("INSERT INTO alert_settings (email_notifications, sms_notifications, push_notifications, email_recipients, sms_recipients, severity_levels, updated_at) VALUES (#{emailNotifications}, #{smsNotifications}, #{pushNotifications}, #{emailRecipients}, #{smsRecipients}, #{severityLevels}, #{updatedAt})")
    void insert(AlertSetting alertSetting);

    @Update("UPDATE alert_settings SET email_notifications = #{emailNotifications}, sms_notifications = #{smsNotifications}, push_notifications = #{pushNotifications}, email_recipients = #{emailRecipients}, sms_recipients = #{smsRecipients}, severity_levels = #{severityLevels}, updated_at = #{updatedAt} WHERE id = #{id}")
    void update(AlertSetting alertSetting);
}
