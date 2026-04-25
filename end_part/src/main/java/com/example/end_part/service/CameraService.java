package com.example.end_part.service;

import com.example.end_part.entity.Camera;
import com.example.end_part.mapper.CameraMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
public class CameraService {

    @Autowired
    private CameraMapper cameraMapper;

    public List<Camera> getList(Map<String, Object> params) {
        return cameraMapper.findAll();
    }

    public Camera getById(Long id) {
        Camera camera = cameraMapper.findById(id);
        if (camera == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Camera not found");
        }
        return camera;
    }

    public String getLiveStream(Long id) {
        return getById(id).getStreamUrl();
    }

    public Camera refreshStatus(Long id) {
        Camera camera = getById(id);
        camera.setUpdatedAt(LocalDateTime.now());
        cameraMapper.update(camera);
        return camera;
    }

    public Camera add(Camera camera) {
        validateCamera(camera);
        camera.setStatus(camera.getStatus() == null || camera.getStatus().isBlank() ? "OFFLINE" : camera.getStatus());
        camera.setLastActive(LocalDateTime.now());
        camera.setCreatedAt(LocalDateTime.now());
        camera.setUpdatedAt(LocalDateTime.now());
        cameraMapper.insert(camera);
        return camera;
    }

    public Camera update(Long id, Camera camera) {
        Camera existingCamera = getById(id);
        validateCamera(camera);
        existingCamera.setName(camera.getName());
        existingCamera.setDeviceId(camera.getDeviceId());
        existingCamera.setIpAddress(camera.getIpAddress());
        existingCamera.setPort(camera.getPort());
        existingCamera.setLocation(camera.getLocation());
        existingCamera.setStreamUrl(camera.getStreamUrl());
        existingCamera.setStatus(camera.getStatus() == null || camera.getStatus().isBlank() ? existingCamera.getStatus() : camera.getStatus());
        existingCamera.setUpdatedAt(LocalDateTime.now());
        cameraMapper.update(existingCamera);
        return existingCamera;
    }

    public void delete(Long id) {
        getById(id);
        cameraMapper.delete(id);
    }

    private void validateCamera(Camera camera) {
        if (camera == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Camera payload is required");
        }
        if (camera.getName() == null || camera.getName().isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Camera name is required");
        }
        if (camera.getDeviceId() == null || camera.getDeviceId().isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "deviceId is required");
        }
    }
}
