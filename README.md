# security_camera_analysis

Software to manage the local disk in the server used to extend a security camera.

Detect objects in security camera footage using YOLOv8.  
Clean up old footage based on detected objects to keep disk space usage low.  
Show captured images to users through a web interface.

## Components

This project contains two main modules:

- **[Video Processing](README_PROCESSING.md)**: Analyze security camera footage using YOLO object detection, manage disk space, and clean up old footage based on detected objects
- **[Web Application](README_WEBAPP.md)**: Web interface to view captured images and browse security camera footage

## Quick Start

```bash
git clone https://github.com/jorritvm/security_camera_analysis.git
cd security_camera_analysis/
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

See the individual component READMEs for detailed usage instructions.

## Author

Jorrit Vander Mynsbrugge 



