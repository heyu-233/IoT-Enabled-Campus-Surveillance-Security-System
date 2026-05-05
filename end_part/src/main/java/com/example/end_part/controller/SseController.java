package com.example.end_part.controller;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@RestController
@RequestMapping("/behaviors")
public class SseController {

    private final List<SseEmitter> emitters = new CopyOnWriteArrayList<>();
    private final List<SseEmitter> lightEmitters = new CopyOnWriteArrayList<>();

    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter subscribe() {
        SseEmitter emitter = new SseEmitter(Long.MAX_VALUE);
        emitters.add(emitter);

        emitter.onCompletion(() -> emitters.remove(emitter));
        emitter.onError(e -> emitters.remove(emitter));
        emitter.onTimeout(() -> emitters.remove(emitter));

        return emitter;
    }

    @GetMapping(value = "/light/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter lightStream() {
        SseEmitter emitter = new SseEmitter(Long.MAX_VALUE);
        lightEmitters.add(emitter);

        emitter.onCompletion(() -> lightEmitters.remove(emitter));
        emitter.onError(e -> lightEmitters.remove(emitter));
        emitter.onTimeout(() -> lightEmitters.remove(emitter));

        return emitter;
    }

    public void broadcast(Object data) {
        List<SseEmitter> deadEmitters = new ArrayList<>();
        emitters.forEach(emitter -> {
            try {
                emitter.send(SseEmitter.event().data(data));
            } catch (IOException e) {
                deadEmitters.add(emitter);
            }
        });
        emitters.removeAll(deadEmitters);
    }

    public void broadcastLightStatus(int alsValue, int level) {
        String data = String.format("{\"alsValue\":%d,\"level\":%d}", alsValue, level);
        List<SseEmitter> deadEmitters = new ArrayList<>();
        lightEmitters.forEach(emitter -> {
            try {
                emitter.send(SseEmitter.event().data(data));
            } catch (IOException e) {
                deadEmitters.add(emitter);
            }
        });
        lightEmitters.removeAll(deadEmitters);
    }
}
