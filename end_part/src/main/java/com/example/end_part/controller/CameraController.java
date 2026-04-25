package com.example.end_part.controller;

import com.example.end_part.entity.Camera;
import com.example.end_part.service.CameraService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/cameras")
public class CameraController {

    @Autowired
    private CameraService cameraService;

    @GetMapping
    public ResponseEntity<List<Camera>> getList(@RequestParam Map<String, Object> params) {
        List<Camera> cameras = cameraService.getList(params);
        return new ResponseEntity<>(cameras, HttpStatus.OK);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Camera> getById(@PathVariable Long id) {
        Camera camera = cameraService.getById(id);
        return new ResponseEntity<>(camera, HttpStatus.OK);
    }

    @GetMapping("/{id}/stream")
    public ResponseEntity<String> getLiveStream(@PathVariable Long id) {
        String streamUrl = cameraService.getLiveStream(id);
        return new ResponseEntity<>(streamUrl, HttpStatus.OK);
    }

    @PostMapping("/{id}/refresh")
    public ResponseEntity<Camera> refreshStatus(@PathVariable Long id) {
        Camera camera = cameraService.refreshStatus(id);
        return new ResponseEntity<>(camera, HttpStatus.OK);
    }

    @PostMapping
    public ResponseEntity<Camera> add(@RequestBody Camera camera) {
        Camera newCamera = cameraService.add(camera);
        return new ResponseEntity<>(newCamera, HttpStatus.CREATED);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Camera> update(@PathVariable Long id, @RequestBody Camera camera) {
        Camera updatedCamera = cameraService.update(id, camera);
        return new ResponseEntity<>(updatedCamera, HttpStatus.OK);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        cameraService.delete(id);
        return new ResponseEntity<>(HttpStatus.NO_CONTENT);
    }
}
