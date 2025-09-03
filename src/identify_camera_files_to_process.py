"""
The goal of this module is to identify which folders need to be processed for object detection.
The main method must be called with a folder path corresponding to an annual upload folder (e.g. T:\reolink\2025)
The script will recurse into all folders and compare the contents to the contents of the detected_objects.json file.
Missing files will be listed as files to be processed.
The output is a list of file paths, one per line.
All configuration is done in the constants.py file.
"""
import os
from utils import setup_logging, log
import json

setup_logging()

def recursively_list_all_video_files_in_folder(folder_path, extensions):
    """
    Recursively list all video files in a folder with given extensions.
    Returns a list of file paths.
    """
    log(f"Listing all video files in folder: {folder_path}")
    video_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(extensions):
                video_files.append(os.path.join(root, file))
    return video_files


def convert_list_of_file_paths_to_dict(file_paths):
    """
    Convert a list of file paths to a dictionary with file paths as keys
    and a list of file names sharing that path as values.
    """
    file_dict = {}
    for file_path in file_paths:
        folder_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        if folder_path not in file_dict:
            file_dict[folder_path] = []
        file_dict[folder_path].append(file_name)
    return file_dict


def filter_file_paths_by_detected_objects(file_dict, detect_objects_filename):
    """
    Filter the file paths by comparing to the detected_objects.json file in each folder.
    Returns a list of file paths.
    """
    files_to_process = []
    for folder_path, file_names in file_dict.items():
        detected_objects_file_path = os.path.join(folder_path, detect_objects_filename)
        if not os.path.exists(detected_objects_file_path):
            for file_name in file_names:
                files_to_process.append(os.path.join(folder_path, file_name))
        else:
            with open(detected_objects_file_path, 'r') as f:
                try:
                    detected_data = json.load(f)
                    processed_files = set(detected_data.keys())
                    for file_name in file_names:
                        if file_name not in processed_files:
                            files_to_process.append(os.path.join(folder_path, file_name))
                except json.JSONDecodeError:
                    for file_name in file_names:
                        files_to_process.append(os.path.join(folder_path, file_name))
    return files_to_process

if __name__ == "__main__":
    """example usage of this module"""
    from config import ROOT_CAMERA_FOLDER_PATH, FORCE_REEVALUATION, VIDEO_FILE_EXTENSIONS, DETECT_OBJECTS_FILENAME

    log("----------------all files to process----------------")
    all_video_file_paths = recursively_list_all_video_files_in_folder(ROOT_CAMERA_FOLDER_PATH, VIDEO_FILE_EXTENSIONS)
    log(all_video_file_paths)

    if not FORCE_REEVALUATION:
       log("----------------filtered files to process----------------")
       all_video_files_as_dict = convert_list_of_file_paths_to_dict(all_video_file_paths)
       filtered_files_to_process = filter_file_paths_by_detected_objects(all_video_files_as_dict, DETECT_OBJECTS_FILENAME)
       log(filtered_files_to_process)


