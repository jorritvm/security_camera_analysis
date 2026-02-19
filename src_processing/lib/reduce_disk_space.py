"""
This module reduces disk space by removing files that did not have certain objects detected in them.
"""

import os
import json
from lib.utils import log

# setup_logging()


def remove_file_without_objects(file_path, detected_objects, target_objects, dry_run):
    """
    Remove a file if it does not have any of the target objects detected in it.
    This function checks the corresponding detected_objects.json file in the same folder.
    When using this function for multiple files you will re-read the .json for every file.
    file_path: path to the file to check and potentially remove.
    detected_objects: set of objects detected in the file.
    target_objects: list of objects to check for (e.g., ['person', 'car']).
    """
    log(f"Evaluating whether to remove file: {file_path}")
    folder_path = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)

    if detected_objects.intersection(target_objects):
        return

    # at this point you are sure your file has been processed and does not contain any of the target objects, so you can remove it
    file_path_to_remove = os.path.join(folder_path, file_name)
    if os.path.exists(file_path_to_remove):
        if not dry_run:
            os.remove(file_path_to_remove)
        log(f"Removed file: {file_path_to_remove}")


def remove_files_without_objects(file_paths, detect_objects_filename, target_objects, dry_run):
    """
    Remove files that do not have any of the target objects detected in them.
    This function checks the corresponding detected_objects.json file in the same folder.
    Files are first grouped per folder. Hence, when using this function for multiple files you will re-read the .json only once per folder.

    file_dict: dictionary with folder paths as keys and a list of file names sharing that path as values.
    detect_objects_filename: name of the JSON file containing detected objects in each folder.
    target_objects: list of objects to check for (e.g., ['person', 'car']).
    """
    file_dict = convert_list_of_file_paths_to_dict(file_paths)
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

            # at this point you are sure your file has been processed and does not contain any of the target objects, so you can remove it
            file_path_to_remove = os.path.join(folder_path, file_name)
            if os.path.exists(file_path_to_remove):
                if not dry_run:
                    os.remove(file_path_to_remove)
                log(f"Removed file: {file_path_to_remove}")


if __name__ == "__main__":
    from config import VIDEO_FILE_EXTENSIONS
    from config import DETECT_OBJECTS_FILENAME, KEEP_VIDEOS_WITH_OBJECTS
    from lib.identify_camera_files_to_process import recursively_list_all_video_files_in_folder, convert_list_of_file_paths_to_dict
    log("Starting disk space reduction process (as dry run)...")
    root_camera_folder_path = r"T:\ftp_reolink\reolink\2025" # specify the root folder path here for this test
    file_paths = recursively_list_all_video_files_in_folder(root_camera_folder_path, VIDEO_FILE_EXTENSIONS)
    remove_files_without_objects(file_paths, DETECT_OBJECTS_FILENAME, KEEP_VIDEOS_WITH_OBJECTS, dry_run=False)