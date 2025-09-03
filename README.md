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
  "day_cars_passing_by.mp4": [
    "truck",
    "car"
  ],
  "day_humans_walking.mp4": [
    "truck",
    "person",
    "skateboard",
    "car"
  ],
  "day_human_arriving_by_car.mp4": [
    "truck",
    "car",
    "train",
    "person"
  ]
}
```

## Performance Evaluation

To benchmark this a series of test videos was selected. Each portrays a different scenario:

 Image                         | Day / Night | Contains Human 
-------------------------------|-------------|----------------
 day_cars_passing_by.mp4       | Day         | ❌              
 day_driving_cars.mp4          | Day         | ❌              
 day_human_arriving_by_car.mp4 | Day         | ✅              
 day_human_cyclist.mp4         | Day         | ✅              
 day_humans_walking.mp4        | Day         | ✅              
 day_nothing_at_all.mp4        | Day         | ❌              
 day_parked_car_humans_cat.mp4 | Day         | ✅              
 night_cat_human_on_bike.mp4   | Night       | ✅              
 night_humans.mp4              | Night       | ✅              
 night_nothing_but_wind.mp4    | Night       | ❌              
 night_parked_car.mp4          | Night       | ❌              

During benchmarking the following metrics were evaluated:

- Accuracy: the proportion of all classifications that were correct.
- Precision: the proportion of all the model's positive classifications that are actually positive.
- False positive rate (FPR): the proportion of all actual negatives that were classified incorrectly as positives.

 System   | Frame_skip | Yolo Model | VSize | Elapsed time | Accuracy | Precision | FPR  
----------|------------|------------|-------|--------------|----------|-----------|------
 R7 5800U | 1          | small      | 1280  | 00:09:49     | 0.91     | 0.83      | 0.10 
 R7 5800U | 3          | small      | 1280  | 00:09:49     | 0.91     | 0.83      | 0.10 
 R7 5800U | 10         | small      | 1280  | 00:09:49     | 0.91     | 0.83      | 0.10 
 R7 5800U | 10         | small      | 1280  | 00:09:49     | 0.91     | 0.83      | 0.10 

## Installation

```bash
git clone https://github.com/jorritvm/security_camera_analysis.git
cd security_camera_analysis/
uv sync
source .venv/bin/activate
```

## Author

Jorrit Vander Mynsbrugge 



