"""
Analyze camera video files in a folder using YOLO object detection model.
1. Recursively list all video files in the specified folder.
2. Convert each video file to a lower resolution for faster processing.
3. Use YOLO model to detect objects in the video file, skipping frames as specified.
4. Persist detected objects to a JSON file in the same folder as the video file.
5. Print detected objects to the console.

Dependencies:
- ultralytics (YOLOv8): pip install ultralytics
- ffmpeg: Install ffmpeg on your system (https://ffmpeg.org/download.html)
"""

import json
import os

import cv2
from ultralytics import YOLO
from utils import setup_logging, log, Timer

setup_logging()


def detect_objects_in_video_files(file_paths: list[str], ffmpeg_temp_folder_path, converted_video_vsize, yolo_model_name,
                                  yolo_threshold, frame_skip, detect_objects_filename):
    """
    Detect objects in video files using YOLO model.
    Returns a dictionary with file paths as keys and sets of detected objects as values.
    """
    yolo_model = create_yolo_model(yolo_model_name)

    log("Processing all video files in folder...")
    results = dict()
    for file_path in file_paths:
        objects = detect_objects_in_video_file(file_path, ffmpeg_temp_folder_path, converted_video_vsize, frame_skip,
                                               yolo_model, yolo_threshold, detect_objects_filename)
        results[file_path] = objects

    return results


def detect_objects_in_video_file(file_path, ffmpeg_temp_folder_path, converted_video_vsize, frame_skip, yolo_model,
                                 yolo_threshold, detect_objects_filename):
    file_name = os.path.basename(file_path)
    log(f"Processing file: {file_name}")
    low_resolution_file_path = convert_video_file_to_lower_resolution(file_path, ffmpeg_temp_folder_path,
                                                                      converted_video_vsize)
    detected_objects = perform_video_file_analysis(low_resolution_file_path, yolo_model, frame_skip,
                                                   yolo_threshold)
    persist_detected_objects(file_path, detected_objects, detect_objects_filename)
    print_detected_objects(detected_objects)
    remove_temporary_low_resolution_file(low_resolution_file_path)
    return detected_objects


def convert_video_file_to_lower_resolution(input_file_path, output_folder_path, converted_video_vsize):
    """converts video file using ffmpeg installed on system to lower resolution and saves it to output folder.
    -vf "scale=1920:1080" → resizes to HD.
    -c:v libx264 → re-encodes video using H.264.
    -crf 23 → controls quality (lower = better quality, bigger file; higher = smaller file).
    -preset fast → balances speed vs compression.
    -an → no audio
    """

    # check if TEMP_FOLDER exists, if not create it
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
    file_name = os.path.basename(input_file_path)
    output_file_path = os.path.join(output_folder_path, file_name)

    log(f"Converting video file to lower resolution: {input_file_path} → {output_file_path}")
    # input file path must resolve to an absolute path, no .. allowed
    input_file_path = os.path.abspath(input_file_path)
    output_file_path = os.path.abspath(output_file_path)
    command = f'ffmpeg -i "{input_file_path}" -vf "scale=-2:{converted_video_vsize}" ' \
              f'-c:v libx264 -crf 23 -preset fast -an "{output_file_path}" -y -loglevel error'
    os.system(command)
    return output_file_path


def create_yolo_model(model_name):
    """Create and return a YOLO model."""
    log(f"Creating YOLO model: {model_name}")
    model = YOLO(model_name)
    return model


def perform_video_file_analysis(video_file_path, model, frame_skip, threshold):
    """Detect objects in a video file using YOLO model. Returns a set of detected object class names."""
    log(f"Starting object detection for file {os.path.basename(video_file_path)}")

    # using cv2 we're building a subset of frames to pass to the model
    cap = cv2.VideoCapture(video_file_path)

    detected_objects = set()
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_skip == 0:
            results = model(frame, verbose=False)
            for box in results[0].boxes:
                cls = model.names[int(box.cls)]
                conf = float(box.conf)
                if conf >= threshold:
                    detected_objects.add(cls)

        frame_idx += 1

    cap.release()
    return detected_objects


def persist_detected_objects(video_file_path, detected_objects, detect_objects_filename):
    """Persist detected objects to a JSON file in the same folder as the video file.
    Append if the file already exists."""
    folder_path = os.path.dirname(video_file_path)
    output_file_path = os.path.join(folder_path, detect_objects_filename)
    log(f"Persisting detected objects to file: {output_file_path}")
    # load existing data if file exists
    if os.path.exists(output_file_path):
        with open(output_file_path, "r") as f:
            existing_data = json.load(f)
    else:
        existing_data = dict()
    # append new data & write to disk
    file_name = os.path.basename(video_file_path)
    existing_data[file_name] = list(detected_objects)
    with open(output_file_path, "w") as f:
        json.dump(existing_data, f, indent=4)


def print_detected_objects(detected_objects):
    """Print the list of detected objects as a oneliner."""
    if detected_objects:
        log("Objects detected: " + ", ".join(detected_objects))
    else:
        log("No objects detected.")


def remove_temporary_low_resolution_file(file_path):
    """Remove the temporary low resolution file."""
    if os.path.exists(file_path):
        os.remove(file_path)
        log(f"Removed temporary file: {file_path}")
    else:
        log(f"Temporary file not found, could not remove: {file_path}")


if __name__ == '__main__':
    # this entrypoint serves as a way of testing the analysis part of the repo

    from config import DETECT_OBJECTS_FILENAME, FRAME_SKIP
    from config import YOLO_MODEL_NAME, YOLO_THRESHOLD, TEMP_FOLDER, CONVERTED_VIDEO_SIZE

    # define video file paths manually for testing
    file_paths = ["../data/demo_clips/day_humans_walking.mp4",
                  "../data/demo_clips/day_nothing_at_all.mp4",
                  "../data/demo_clips/night_humans.mp4"]

    # execute the video file analysis
    timer = Timer("Total processing time")
    timer.start()
    all_detected_objects = detect_objects_in_video_files(file_paths, TEMP_FOLDER, CONVERTED_VIDEO_SIZE, YOLO_MODEL_NAME,
                                                         YOLO_THRESHOLD, FRAME_SKIP, DETECT_OBJECTS_FILENAME)
    timer.stop()
    log(timer.elapsed())

    # print file names with 'person' in the detected objects
    log("Files with detected persons:")
    for file_path, objects in all_detected_objects.items():
        file_name = os.path.basename(file_path)
        if 'person' in objects:
            log(f"{file_name}: {', '.join(objects)}")
