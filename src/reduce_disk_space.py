"""
This module reduces disk space by removing files that did not have certain objects detected in them.
"""

import os
import json
from utils import setup_logging, log

setup_logging()

def remove_files_without_objects(file_dict, detect_objects_filename, target_objects, dry_run):
    """
    Remove files that do not have any of the target objects detected in them.
    file_dict: dictionary with folder paths as keys and a list of file names sharing that path as values.
    detect_objects_filename: name of the JSON file containing detected objects in each folder.
    target_objects: list of objects to check for (e.g., ['person', 'car']).
    """
    for folder_path, file_names in file_dict.items():
        # check availability of video analysis results
        detected_objects_file_path = os.path.join(folder_path, detect_objects_filename)
        if not os.path.exists(detected_objects_file_path):
            continue

        # load detected objects data from analysis output
        with open(detected_objects_file_path, 'r') as f:
            try:
                detected_data = json.load(f)
            except json.JSONDecodeError:
                continue

        for file_name in file_names:
            if file_name not in detected_data:
                continue

            detected_objects = set(detected_data[file_name])
            if detected_objects.intersection(target_objects):
                continue

            file_path_to_remove = os.path.join(folder_path, file_name)
            if os.path.exists(file_path_to_remove):
                if not dry_run:
                    os.remove(file_path_to_remove)
                log(f"Removed file: {file_path_to_remove}")


if __name__ == "__main__":
    from config import VIDEO_FILE_EXTENSIONS
    from config import DETECT_OBJECTS_FILENAME, KEEP_VIDEOS_WITH_OBJECTS
    from identify_camera_files_to_process import recursively_list_all_video_files_in_folder, convert_list_of_file_paths_to_dict
    log("Starting disk space reduction process (as dry run)...")
    root_camera_folder_path = "" # specify the root folder path here for this test
    file_paths = recursively_list_all_video_files_in_folder(root_camera_folder_path, VIDEO_FILE_EXTENSIONS)
    file_dict = convert_list_of_file_paths_to_dict(file_paths)
    remove_files_without_objects(file_dict, DETECT_OBJECTS_FILENAME, KEEP_VIDEOS_WITH_OBJECTS, dry_run=True)