# security_camera_analysis
Detect objects in security camera footage.  
Clean up old footage based on detected objects to keep disk space usage low.

## Modules
- (todo) identify_camera_files_to_process.py: selection logic tailored to how reolink organizes their FTP uploads
- analyse_images.py: analyzes the provided image files and generated a report per folder of detected objects
- (todo) reduce_disk_space.py: deletes old images based on retention policy and detected objects

## Example of JSON output from object detection
```json
{
    "cat_bike_night.mp4": [
        "dog",
        "car",
        "person"
    ],
    "cyclist.mp4": [
        "motorcycle",
        "bicycle",
        "person"
    ],
    "driving_cars.mp4": [
        "truck",
        "car"
    ],
    "humans_walking.mp4": [
        "skateboard",
        "truck",
        "car",
        "person"
    ],
    "human_arriving_by_car.mp4": [
        "truck",
        "car",
        "person"
    ],
    "nothing_but_parked_car.mp4": [
        "car"
    ],
    "nothing_but_wind.mp4": []
}
```

## Performance Evaluation
System | Frame_skip | Yolo Model | Converted video size | Elapsed time | Correctess
-------|------------|------------|----------------------|--------------|-----------
AMD Ryzen 7 5800U | 1 | small | 1280 | 00:09:49   | TODO: define benchmark script 


## Installation
```bash
git clone https://github.com/jorritvm/security_camera_analysis.git
cd security_camera_analysis/
uv sync
source .venv/bin/activate
```

## Author
Jorrit Vander Mynsbrugge 



