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
import logging
import os

from ultralytics import YOLO

from config import ROOT_CAMERA_FOLDER_PATH, YOLO_MODEL_NAME, YOLO_THRESHOLD, TEMP_FOLDER, CONVERTED_VIDEO_SIZE
from config import DETECT_OBJECTS_FILENAME, FRAME_SKIP
from utils import setup_logging, log, Timer

setup_logging()

def main_workflow():
    file_paths = recursively_list_all_video_files_in_folder(ROOT_CAMERA_FOLDER_PATH)
    yolo_model = create_yolo_model(YOLO_MODEL_NAME)

    log("Processing all video files in folder...")
    results = dict()
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        log(f"Processing file: {file_name}")
        low_resolution_file_path = convert_video_file_to_lower_resolution(file_path, TEMP_FOLDER)
        detected_objects = detect_objects_in_video_file(low_resolution_file_path, yolo_model, FRAME_SKIP, YOLO_THRESHOLD)
        persist_detected_objects(file_path, detected_objects)
        print_detected_objects(detected_objects)
        results[file_path] = detected_objects
        remove_temporary_low_resolution_file(low_resolution_file_path)

    return results

def recursively_list_all_video_files_in_folder(folder_path, extensions=('.mp4', '.avi', '.mov', '.mkv')):
    """Recursively list all video files in a folder with given extensions. Returns a list of file paths."""
    log(f"Listing all video files in folder: {folder_path}")
    video_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(extensions):
                video_files.append(os.path.join(root, file))
    return video_files


def convert_video_file_to_lower_resolution(input_file_path, output_folder_path):
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
    command = f'ffmpeg -i "{input_file_path}" -vf "scale={CONVERTED_VIDEO_SIZE}:-2" ' \
              f'-c:v libx264 -crf 23 -preset fast -an "{output_file_path}" -y -loglevel error'
    os.system(command)
    return output_file_path


def create_yolo_model(model_name):
    """Create and return a YOLO model."""
    log(f"Creating YOLO model: {model_name}")
    model = YOLO(model_name)
    return model


def detect_objects_in_video_file(video_file_path, model, frame_skip, threshold):
    """Detect objects in a video file using YOLO model. Returns a set of detected object class names."""
    log(f"Starting object detection for file {os.path.basename(video_file_path)}")
    results = model(video_file_path, stream=True, verbose=False)

    detected_objects = set()
    for i, frame in enumerate(results):
        if i % frame_skip == 0:
            for box in frame.boxes:
                cls = model.names[int(box.cls)]
                conf = float(box.conf)
                if conf >= threshold:
                    detected_objects.add(cls)
    return detected_objects


def persist_detected_objects(video_file_path, detected_objects):
    """Persist detected objects to a JSON file in the same folder as the video file.
    Append if the file already exists."""
    folder_path = os.path.dirname(video_file_path)
    output_file_path = os.path.join(folder_path, DETECT_OBJECTS_FILENAME)
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
    timer = Timer("Total processing time")
    timer.start()
    all_detected_objects = main_workflow()
    timer.stop()
    log(timer.elapsed())

    # print file names with 'person' in the detected objects
    log("Files with detected persons:")
    for file_path, objects in all_detected_objects.items():
        file_name = os.path.basename(file_path)
        if 'person' in objects:
            log(f"{file_name}: {', '.join(objects)}")
