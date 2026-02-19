"""
Entrypoint module to run the daily disk space management workflow.
All configuration will be read from config.py
For more documentation look at the readme.
This is designed to run daily as a batch job.
"""

import os
from config import (
    ROOT_CAMERA_FOLDER_PATH, FORCE_REEVALUATION, VIDEO_FILE_EXTENSIONS, DETECT_OBJECTS_FILENAME,
    YOLO_MODEL_NAME, FRAME_SKIP, YOLO_THRESHOLD, TEMP_FOLDER, CONVERTED_VIDEO_SIZE,
    SAVE_STILLS, KEEP_VIDEOS_WITH_OBJECTS, DELETE_DRY_RUN,
    RECENT_FILES_MAX_SIZE_GB, HISTORICAL_FILES_MAX_SIZE_GB, FREE_SPACE_BUFFER_GB
)
from lib.identify_camera_files_to_process import recursively_list_all_video_files_in_folder, filter_unprocessed_file_paths
from lib.analyse_camera_file import create_yolo_model, detect_objects_in_video_file
from lib.utils import setup_logging, log
import json

setup_logging()


def get_file_size_gb(file_path):
    """Get file size in GB."""
    try:
        return os.path.getsize(file_path) / (1024**3)
    except OSError:
        return 0.0

def get_file_info_with_metadata(file_path, detect_objects_filename):
    """
    Get file information including size, modification time, and detected objects.
    Returns a dict with file_path, size_gb, mtime, and detected_objects (set).
    """
    try:
        stat_info = os.stat(file_path)
        size_gb = stat_info.st_size / (1024**3)
        mtime = stat_info.st_mtime

        # Load detected objects from JSON
        folder_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        detected_objects_file_path = os.path.join(folder_path, detect_objects_filename)
        detected_objects = set()

        if os.path.exists(detected_objects_file_path):
            try:
                with open(detected_objects_file_path, 'r') as f:
                    detected_data = json.load(f)
                    if file_name in detected_data:
                        detected_objects = set(detected_data[file_name])
            except (json.JSONDecodeError, KeyError):
                pass

        return {
            'file_path': file_path,
            'size_gb': size_gb,
            'mtime': mtime,
            'detected_objects': detected_objects
        }
    except OSError:
        return None

def remove_file_and_log(file_path, reason, dry_run):
    """Remove a file with logging."""
    if os.path.exists(file_path):
        if not dry_run:
            os.remove(file_path)
        log(f"[{reason}] Removed file: {file_path}")
        return True
    return False

def process_new_files(yolo_model):
    """
    Step 1: Process all new/unprocessed files with YOLO detection.
    Returns the list of all video file paths.
    """
    log("=" * 80)
    log("STEP 1: Processing new/unprocessed video files")
    log("=" * 80)

    all_video_file_paths = recursively_list_all_video_files_in_folder(ROOT_CAMERA_FOLDER_PATH, VIDEO_FILE_EXTENSIONS)
    log(f"Found {len(all_video_file_paths)} video files in total")

    filtered_files_to_process = all_video_file_paths
    if not FORCE_REEVALUATION:
        filtered_files_to_process = filter_unprocessed_file_paths(all_video_file_paths, DETECT_OBJECTS_FILENAME)
    log(f"After filtering, {len(filtered_files_to_process)} files need to be processed")

    for idx, file_path in enumerate(filtered_files_to_process, 1):
        log(f"Processing file {idx}/{len(filtered_files_to_process)}")
        detect_objects_in_video_file(
            file_path, TEMP_FOLDER, CONVERTED_VIDEO_SIZE, FRAME_SKIP,
            yolo_model, YOLO_THRESHOLD, DETECT_OBJECTS_FILENAME, SAVE_STILLS
        )

    log(f"Completed processing {len(filtered_files_to_process)} new files")
    return all_video_file_paths

def manage_disk_space(all_video_file_paths):
    """
    Step 2 & 3: Manage disk space by:
    - Keeping recent files (up to RECENT_FILES_MAX_SIZE_GB), but removing non-target-object videos
    - Keeping older files with target objects (up to HISTORICAL_FILES_MAX_SIZE_GB)
    """
    log("=" * 80)
    log("STEP 2 & 3: Managing disk space")
    log("=" * 80)

    # Gather file information
    log("Gathering file information and metadata...")
    file_info_list = []
    for file_path in all_video_file_paths:
        info = get_file_info_with_metadata(file_path, DETECT_OBJECTS_FILENAME)
        if info:
            file_info_list.append(info)

    # Sort by modification time (newest first)
    file_info_list.sort(key=lambda x: x['mtime'], reverse=True)
    log(f"Total files to evaluate: {len(file_info_list)}")

    # Phase 1: Identify recent files (up to RECENT_FILES_MAX_SIZE_GB) - keep ALL of them
    log(f"\nPhase 1: Identifying recent files (target: {RECENT_FILES_MAX_SIZE_GB} GB)")
    recent_size_gb = 0.0
    recent_index = 0

    for idx, file_info in enumerate(file_info_list):
        recent_size_gb += file_info['size_gb']
        recent_index = idx + 1

        if recent_size_gb >= RECENT_FILES_MAX_SIZE_GB:
            break

    log(f"Recent set: {recent_index} files, {recent_size_gb:.2f} GB (all kept untouched)")

    # Phase 2: Process historical files (files older than the recent set)
    log(f"\nPhase 2: Processing historical files (remove files without target objects)")
    historical_files = file_info_list[recent_index:]
    log(f"Historical files to evaluate: {len(historical_files)}")

    # First pass: Remove files without target objects from historical set
    historical_files_with_targets = []
    historical_removed_no_target = 0

    for file_info in historical_files:
        has_target_objects = bool(file_info['detected_objects'].intersection(KEEP_VIDEOS_WITH_OBJECTS))

        if has_target_objects:
            historical_files_with_targets.append(file_info)
        else:
            if remove_file_and_log(file_info['file_path'], "HISTORICAL_NO_TARGET", DELETE_DRY_RUN):
                historical_removed_no_target += 1

    log(f"Removed {historical_removed_no_target} historical files without target objects")
    log(f"Remaining historical files with target objects: {len(historical_files_with_targets)}")

    # Phase 3: Cap historical files with target objects at HISTORICAL_FILES_MAX_SIZE_GB
    log(f"\nPhase 3: Capping historical files at {HISTORICAL_FILES_MAX_SIZE_GB} GB")
    historical_size_gb = 0.0
    historical_kept = 0
    historical_removed_over_limit = 0

    for file_info in historical_files_with_targets:
        if historical_size_gb < HISTORICAL_FILES_MAX_SIZE_GB:
            # Keep this file
            historical_size_gb += file_info['size_gb']
            historical_kept += 1
        else:
            # Remove this file - over the historical limit
            if remove_file_and_log(file_info['file_path'], "HISTORICAL_OVER_LIMIT", DELETE_DRY_RUN):
                historical_removed_over_limit += 1

    log(f"Historical set after size cap: {historical_kept} files kept, {historical_size_gb:.2f} GB")
    log(f"Removed {historical_removed_over_limit} files due to exceeding historical size limit")

    # Summary
    log("=" * 80)
    log("DISK SPACE MANAGEMENT SUMMARY")
    log("=" * 80)
    log(f"Recent files (all kept): ~{recent_size_gb:.2f} GB (target: {RECENT_FILES_MAX_SIZE_GB} GB)")
    log(f"Historical files (with target objects only): ~{historical_size_gb:.2f} GB (target: {HISTORICAL_FILES_MAX_SIZE_GB} GB)")
    log(f"Total used: ~{recent_size_gb + historical_size_gb:.2f} GB")
    log(f"Expected free space: ~{930 - recent_size_gb - historical_size_gb:.2f} GB "
        f"(target buffer: {FREE_SPACE_BUFFER_GB} GB)")
    log(f"Total files removed: {historical_removed_no_target + historical_removed_over_limit}")

def run_daily_workflow():
    """Main workflow to run daily."""
    log("=" * 80)
    log("STARTING DAILY DISK SPACE MANAGEMENT WORKFLOW")
    log("=" * 80)
    log(f"Root folder: {ROOT_CAMERA_FOLDER_PATH}")
    log(f"Recent files max size: {RECENT_FILES_MAX_SIZE_GB} GB")
    log(f"Historical files max size: {HISTORICAL_FILES_MAX_SIZE_GB} GB")
    log(f"Target free space buffer: {FREE_SPACE_BUFFER_GB} GB")
    log(f"Keep videos with objects: {KEEP_VIDEOS_WITH_OBJECTS}")
    log(f"Dry run mode: {DELETE_DRY_RUN}")
    log("")

    # Step 1: Process new files
    yolo_model = create_yolo_model(YOLO_MODEL_NAME)
    all_video_file_paths = process_new_files(yolo_model)

    # Step 2 & 3: Manage disk space
    manage_disk_space(all_video_file_paths)

    log("=" * 80)
    log("DAILY WORKFLOW COMPLETED")
    log("=" * 80)

if __name__ == "__main__":
    run_daily_workflow()

