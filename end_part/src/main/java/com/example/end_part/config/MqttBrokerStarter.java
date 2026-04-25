package com.example.end_part.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.IOException;
import java.lang.ProcessBuilder.Redirect;

@Component
public class MqttBrokerStarter implements ApplicationRunner, DisposableBean {

    private static final Logger logger = LoggerFactory.getLogger(MqttBrokerStarter.class);
    private static Process mosquittoProcess;

    @Value("${mqtt.broker.autostart:false}")
    private boolean autoStart;

    @Value("${mqtt.broker.binary:F:/Mosquitto/mosquitto.exe}")
    private String brokerBinary;

    @Value("${mqtt.broker.config:F:/Mosquitto/mosquitto.conf}")
    private String brokerConfig;

    @Override
    public void run(ApplicationArguments args) {
        if (autoStart) {
            startMqttBroker();
        } else {
            logger.info("MQTT broker auto-start disabled; expecting external broker.");
        }
    }

    public void startMqttBroker() {
        File binary = new File(brokerBinary);
        File config = new File(brokerConfig);
        if (!binary.exists() || !config.exists()) {
            logger.warn("Skipping broker auto-start because broker binary or config is missing.");
            return;
        }

        try {
            ProcessBuilder processBuilder = new ProcessBuilder(binary.getAbsolutePath(), "-v", "-c", config.getAbsolutePath());
            processBuilder.redirectOutput(Redirect.INHERIT);
            processBuilder.redirectError(Redirect.INHERIT);
            mosquittoProcess = processBuilder.start();
            Thread.sleep(2000);
            logger.info("Mosquitto broker started.");
        } catch (IOException | InterruptedException e) {
            logger.warn("Failed to auto-start Mosquitto broker: {}", e.getMessage());
            Thread.currentThread().interrupt();
        }
    }

    @Override
    public void destroy() throws Exception {
        stopMqttBroker();
    }

    public static void stopMqttBroker() {
        if (mosquittoProcess != null && mosquittoProcess.isAlive()) {
            try {
                mosquittoProcess.destroy();
                mosquittoProcess.waitFor();
                logger.info("Mosquitto broker stopped.");
            } catch (InterruptedException e) {
                logger.error("Failed to stop Mosquitto broker cleanly.", e);
                Thread.currentThread().interrupt();
            }
        }
    }
}
