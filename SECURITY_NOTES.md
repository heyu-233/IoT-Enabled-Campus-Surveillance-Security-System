# Security Notes

This repository was prepared for public GitHub upload.

## Sanitization choices

- Removed reports, presentations, ZIP archives, and other non-code materials
- Removed local build outputs, package directories, runtime logs, and temporary artifacts
- Replaced hard-coded passwords and deployment-specific values with environment variables or safe placeholders
- Removed personal absolute paths and private lab network details where they were not required for understanding the code

## Remaining binary asset

- `end_part/video_stream/best.pt` is intentionally kept because it is the active inference model used by the project

## Before you run

Create your own local environment configuration and do not commit real secrets,
private IP plans, or personal documents back into the repository.
