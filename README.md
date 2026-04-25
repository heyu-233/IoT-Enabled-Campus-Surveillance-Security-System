# IoT-Enabled Campus Surveillance Security System

This repository contains the code used for an embedded campus surveillance demo.
It combines camera-side video capture, RTMP streaming, YOLO-based detection, a
Spring Boot backend, and a Vue frontend.

## Included modules

- `camera/`: i.MX6ULL-side V4L2 capture, H.264 encoding, RTMP push, and edge scripts
- `end_part/`: Spring Boot backend and Windows-side video detection scripts
- `frontend/`: Vue-based monitoring and management UI
- `scripts/`: local helper scripts for setup and development
- `nginx-1.19.3/conf/nginx.conf`: RTMP and HTTP-FLV streaming configuration

## What is included

- Project source code
- Current inference model: `end_part/video_stream/best.pt`
- Minimal configuration needed to reproduce the software setup

## What is intentionally excluded

This public-safe repository does not include:

- thesis reports, project proposals, presentation slides, or support ZIP files
- raw datasets, training caches, experiment folders, or large package mirrors
- personal deployment notes, private IP layouts, local absolute paths, or fixed credentials

## Quick start

### Frontend

```powershell
cd frontend
npm install
npm run build
```

### Backend

1. Copy values from `.env.example` into your own environment.
2. Start MySQL and MQTT services.
3. Run the backend:

```powershell
cd end_part
.\mvnw spring-boot:run
```

### Detector supervisor

```powershell
cd end_part\video_stream
python yolo_inference_windows.py --model best.pt --fps 5
```

### Camera-side code

The camera module is designed for an embedded Linux board. Update the runtime
variables in the shell scripts or export them from your environment before use.

## Notes

- Default configuration now uses local-safe placeholders and environment variables.
- If you publish this repository, keep your real credentials and deployment files out of Git.
