# Webapp

## Introduction
The webapp uses Flask and Jinja2 templates to show captured images from security cameras.
For layouting bootstrap 5 is used.

## Installation

```bash
git clone https://github.com/jorritvm/security_camera_analysis.git
cd security_camera_analysis/
uv sync
source .venv/bin/activate
```

## Usage
To run the webapp locally:
```bash
cd src_webapp/
python app.py
```

## Docker
To build and run the webapp in docker.
Set up BASE_DIR to /app/images!!! Mount it in that location at runtime.
Then run:
```bash
cd src_webapp/
docker build -t security_camera_webapp .
docker run -v "e:\ftp_reolink\reolink":/app/images -p 8080:5000 --name security_camera_webapp_container security_camera_webapp
```
