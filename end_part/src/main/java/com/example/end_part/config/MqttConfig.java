package com.example.end_part.config;

import com.example.end_part.service.MqttMessageService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class MqttConfig {

    private static final Logger logger = LoggerFactory.getLogger(MqttConfig.class);

    @Value("${mqtt.broker.url}")
    private String brokerUrl;

    @Value("${mqtt.client.id}")
    private String clientId;

    @Value("${mqtt.username:}")
    private String username;

    @Value("${mqtt.password:}")
    private String password;

    @Value("${mqtt.qos:1}")
    private int qos;

    @Value("${mqtt.topic.edge:edge/#}")
    private String edgeTopic;

    @Value("${mqtt.topic.sensors:sensors/+}")
    private String sensorsTopic;

    @Autowired
    private MqttMessageService mqttMessageService;

    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper();
    }

    @Bean
    public MqttClient mqttClient() throws MqttException {
        MqttClient client = new MqttClient(brokerUrl, clientId, new MemoryPersistence());
        MqttConnectOptions options = buildOptions();

        client.setCallback(new MqttCallback() {
            @Override
            public void connectionLost(Throwable cause) {
                logger.error("MQTT connection lost", cause);
                reconnectAsync(client, options);
            }

            @Override
            public void messageArrived(String topic, MqttMessage message) {
                try {
                    mqttMessageService.handleMessage(topic, new String(message.getPayload()));
                } catch (Exception e) {
                    logger.error("Failed to handle MQTT message", e);
                }
            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken token) {
                logger.debug("MQTT delivery complete: {}", token.getMessageId());
            }
        });

        try {
            client.connect(options);
            client.subscribe(edgeTopic, qos);
            client.subscribe(sensorsTopic, qos);
            logger.info("MQTT connected and subscribed to {} and {}", edgeTopic, sensorsTopic);
        } catch (MqttException e) {
            logger.warn("Initial MQTT connection failed, retrying in background: {}", e.getMessage());
            reconnectAsync(client, options);
        }

        return client;
    }

    @Bean
    public MqttPublisher mqttPublisher(MqttClient mqttClient) {
        return new MqttPublisher(mqttClient, qos);
    }

    private MqttConnectOptions buildOptions() {
        MqttConnectOptions options = new MqttConnectOptions();
        options.setCleanSession(true);
        options.setConnectionTimeout(30);
        options.setKeepAliveInterval(60);
        if (username != null && !username.isEmpty()) {
            options.setUserName(username);
        }
        if (password != null && !password.isEmpty()) {
            options.setPassword(password.toCharArray());
        }
        return options;
    }

    private void reconnectAsync(MqttClient client, MqttConnectOptions options) {
        new Thread(() -> {
            for (int retry = 1; retry <= 10; retry++) {
                try {
                    Thread.sleep(3000);
                    if (!client.isConnected()) {
                        client.connect(options);
                        client.subscribe(edgeTopic, qos);
                        client.subscribe(sensorsTopic, qos);
                        logger.info("MQTT reconnected on attempt {}", retry);
                        return;
                    }
                } catch (Exception e) {
                    logger.warn("MQTT reconnect attempt {} failed: {}", retry, e.getMessage());
                }
            }
        }, "mqtt-reconnect").start();
    }

    public static class MqttPublisher {
        private final MqttClient mqttClient;
        private final int qos;

        public MqttPublisher(MqttClient mqttClient, int qos) {
            this.mqttClient = mqttClient;
            this.qos = qos;
        }

        public void publish(String topic, String payload) throws MqttException {
            MqttMessage message = new MqttMessage(payload.getBytes());
            message.setQos(qos);
            mqttClient.publish(topic, message);
        }
    }
}
