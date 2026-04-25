package com.example.end_part.service;

import com.example.end_part.dto.EdgeCommandResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.LocalDateTime;

@Service
public class DetectorSupervisorClient {

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(3))
            .build();

    @Value("${detector.supervisor.base-url:http://127.0.0.1:19090}")
    private String supervisorBaseUrl;

    public EdgeCommandResponse start(String deviceId) {
        return post("/start", "{\"device_id\":\"" + deviceId + "\"}", "Detector started");
    }

    public EdgeCommandResponse stop(String deviceId) {
        return post("/stop", "{\"device_id\":\"" + deviceId + "\"}", "Detector stopped");
    }

    public EdgeCommandResponse config(String deviceId, String payload) {
        String requestBody = payload != null && !payload.isBlank()
                ? payload
                : "{\"device_id\":\"" + deviceId + "\"}";
        return post("/config", requestBody, "Detector config updated");
    }

    public EdgeCommandResponse status() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(supervisorBaseUrl + "/status"))
                    .timeout(Duration.ofSeconds(5))
                    .GET()
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            boolean success = response.statusCode() >= 200 && response.statusCode() < 300;
            return new EdgeCommandResponse(success, response.body(), LocalDateTime.now());
        } catch (IOException | InterruptedException e) {
            if (e instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
            return new EdgeCommandResponse(false, e.getMessage(), LocalDateTime.now());
        }
    }

    private EdgeCommandResponse post(String path, String requestBody, String successMessage) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(supervisorBaseUrl + path))
                    .timeout(Duration.ofSeconds(5))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody, StandardCharsets.UTF_8))
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            boolean success = response.statusCode() >= 200 && response.statusCode() < 300;
            String message = success ? successMessage : response.body();
            return new EdgeCommandResponse(success, message, LocalDateTime.now());
        } catch (IOException | InterruptedException e) {
            if (e instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
            return new EdgeCommandResponse(false, e.getMessage(), LocalDateTime.now());
        }
    }
}
