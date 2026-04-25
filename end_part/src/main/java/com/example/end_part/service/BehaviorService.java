package com.example.end_part.service;

import com.example.end_part.controller.SseController;
import com.example.end_part.entity.Behavior;
import com.example.end_part.mapper.BehaviorMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
public class BehaviorService {

    @Autowired
    private BehaviorMapper behaviorMapper;

    @Autowired
    private SseController sseController;

    public List<Behavior> getList(Map<String, Object> params) {
        return behaviorMapper.findAll();
    }

    public Behavior getById(Long id) {
        return behaviorMapper.findById(id);
    }

    public void remove(Long id) {
        behaviorMapper.delete(id);
    }

    public Behavior addBehavior(Behavior behavior) {
        behavior.setCreatedAt(LocalDateTime.now());
        behaviorMapper.insert(behavior);
        sseController.broadcast(behavior);
        return behavior;
    }
}
