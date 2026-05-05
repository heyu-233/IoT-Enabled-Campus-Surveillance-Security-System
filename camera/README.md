# Linux Camera Appendix Package

This folder is a submission-oriented appendix package for the graduation project.
It collects the final runnable scripts and a cleaner, modularized version of the
core video pipeline source code.

## Directory Layout

- `Makefile`
  - Example build entry for the two demo programs.
- `README.md`
  - This file.
- `v4l2_rtmp_push.c`
  - Main program for `V4L2 -> H.264 -> FLV -> RTMP`.
- `v4l2_h264_capture.c`
  - Single-file local H.264 verification program.
- `capture.h`, `capture.c`
  - V4L2 capture front-end and `YUYV -> YUV420P` conversion.
- `encoder.h`, `encoder.c`
  - H.264 encoder based on `libx264/libavcodec`.
- `rtmp.h`, `rtmp.c`
  - FLV/RTMP output module based on `libavformat`.
- `edge_agent.sh`
  - MQTT edge control agent.
- `start_edge_agent.sh`
  - Startup wrapper that prepares network and launches the agent.
- `net_up.sh`
  - Static IP network bootstrap script for the board.

## Functional Summary

This appendix corresponds to the final validated pipeline:

`/dev/video0 -> YUYV -> YUV420P -> H.264 -> FLV -> RTMP -> nginx-rtmp -> HTTP-FLV`

The MQTT control topics currently used are:

- subscribe: `edge/stream/start`
- subscribe: `edge/stream/stop`
- subscribe: `edge/buzzer/on`
- subscribe: `edge/buzzer/off`
- subscribe: `edge/led/blink`
- publish: `edge/heartbeat`

## Build Notes

The source is intended for cross-compiling on Ubuntu for the i.MX6ULL board.

### Example build

For the modular RTMP push version:

```sh
make v4l2_rtmp_push \
    CC=arm-linux-gnueabihf-gcc \
    FFMPEG_PREFIX=/path/to/ffmpeg_arm_install \
    X264_PREFIX=/path/to/x264_arm_install
```

For the local H.264 verification version:

```sh
make v4l2_h264_capture \
    CC=arm-linux-gnueabihf-gcc \
    FFMPEG_PREFIX=/path/to/ffmpeg_arm_install \
    X264_PREFIX=/path/to/x264_arm_install
```

## Runtime Notes

- Board video node used in the validated setup: `/dev/video0`
- Board static IP used in the validated setup: `192.168.1.2`
- Windows host Ethernet IP used in the validated setup: `192.168.1.10`
- RTMP URL used in the validated setup:

```text
rtmp://192.168.1.10:1935/myapp/stream
```

- MQTT broker used in the validated setup:

```text
192.168.1.10:1883
```

## Appendix Intention

This package is not meant to replace the full project repository. It is a clean
appendix view intended for:

- graduation report appendix
- code structure explanation
- demo reproduction notes
- oral defense walkthrough
