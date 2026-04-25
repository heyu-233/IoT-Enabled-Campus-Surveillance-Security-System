package com.example.end_part.controller;

import com.example.end_part.entity.Behavior;
import com.example.end_part.service.BehaviorService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/behaviors")
public class BehaviorController {

    @Autowired
    private BehaviorService behaviorService;

    @GetMapping
    public ResponseEntity<List<Behavior>> getList(@RequestParam Map<String, Object> params) {
        List<Behavior> behaviors = behaviorService.getList(params);
        return new ResponseEntity<>(behaviors, HttpStatus.OK);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Behavior> getById(@PathVariable Long id) {
        Behavior behavior = behaviorService.getById(id);
        return new ResponseEntity<>(behavior, HttpStatus.OK);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> remove(@PathVariable Long id) {
        behaviorService.remove(id);
        return new ResponseEntity<>(HttpStatus.NO_CONTENT);
    }

    @PostMapping
    public ResponseEntity<Behavior> add(@RequestBody Behavior behavior) {
        Behavior createdBehavior = behaviorService.addBehavior(behavior);
        return new ResponseEntity<>(createdBehavior, HttpStatus.CREATED);
    }
}
