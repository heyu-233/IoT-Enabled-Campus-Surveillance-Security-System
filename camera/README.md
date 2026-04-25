# Camera Module

This directory contains the embedded camera-side capture and streaming code used
by the campus surveillance demo.

## Included files

- `v4l2_rtmp_push.c`: main `V4L2 -> H.264 -> FLV -> RTMP` pipeline
- `v4l2_h264_capture.c`: local H.264 capture test program
- `capture.*`: V4L2 capture and pixel conversion helpers
- `encoder.*`: H.264 encoding helpers
- `rtmp.*`: RTMP output helpers
- `edge_agent.sh`: MQTT-based edge control script
- `start_edge_agent.sh`: startup wrapper for the edge agent
- `net_up.sh`: optional static network helper for the board

## Pipeline overview

The validated camera-side flow is:

`/dev/video0 -> YUYV -> YUV420P -> H.264 -> FLV -> RTMP -> nginx-rtmp -> HTTP-FLV`

Control messages use MQTT topics such as:

- `edge/stream/start`
- `edge/stream/stop`
- `edge/buzzer/on`
- `edge/buzzer/off`
- `edge/led/blink`
- `edge/heartbeat`

## Build example

```sh
make v4l2_rtmp_push \
    CC=arm-linux-gnueabihf-gcc \
    FFMPEG_PREFIX=/path/to/ffmpeg_arm_install \
    X264_PREFIX=/path/to/x264_arm_install
```

## Configuration note

This public repository removes personal deployment details. Set the RTMP target,
MQTT broker, and board network configuration for your own environment before
running the scripts.
