"""
Entrypoint module to run the code in production mode
All confioguration will be read from frm config.py

The workflow will try to process file by file, instead of first analysing all files and only then doing the cleanup.
"""

from config import ROOT_CAMERA_FOLDER_PATH, FORCE_REEVALUATION, VIDEO_FILE_EXTENSIONS, DETECT_OBJECTS_FILENAME, \
    YOLO_MODEL_NAME, FRAME_SKIP, YOLO_THRESHOLD, TEMP_FOLDER, CONVERTED_VIDEO_SIZE, SAVE_STILLS, KEEP_VIDEOS_WITH_OBJECTS, DELETE_DRY_RUN

from lib.identify_camera_files_to_process import recursively_list_all_video_files_in_folder, filter_unprocessed_file_paths
from lib.analyse_camera_file import create_yolo_model, detect_objects_in_video_file
from lib.reduce_disk_space import remove_file_without_objects
from lib.utils import setup_logging, log

setup_logging()

def run_production_workflow():
    # identify files to process
    all_video_file_paths = recursively_list_all_video_files_in_folder(ROOT_CAMERA_FOLDER_PATH, VIDEO_FILE_EXTENSIONS)
    log(f"Found {len(all_video_file_paths)} video files in total")
    filtered_files_to_process = all_video_file_paths
    if not FORCE_REEVALUATION:
        filtered_files_to_process = filter_unprocessed_file_paths(all_video_file_paths, DETECT_OBJECTS_FILENAME)
    log(f"After filtering, {len(filtered_files_to_process)} files remain to be processed")

    yolo_model = create_yolo_model(YOLO_MODEL_NAME)
    for file_path in filtered_files_to_process:
        # analyse the file
        objects_set = detect_objects_in_video_file(file_path, TEMP_FOLDER, CONVERTED_VIDEO_SIZE, FRAME_SKIP,
                                     yolo_model, YOLO_THRESHOLD, DETECT_OBJECTS_FILENAME, SAVE_STILLS)

        # remove files without desired objects
        remove_file_without_objects(file_path, objects_set, KEEP_VIDEOS_WITH_OBJECTS, DELETE_DRY_RUN)


if __name__ == "__main__":
    run_production_workflow()
