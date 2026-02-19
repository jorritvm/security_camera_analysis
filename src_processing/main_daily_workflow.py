"""
Entrypoint module to run the daily disk space management workflow.
All configuration will be read from config.py
For more documentation look at the readme.
This is designed to run daily as a batch job.
"""

import os
import re
import shutil
from config import (
    ROOT_CAMERA_FOLDER_PATH, FORCE_REEVALUATION, VIDEO_FILE_EXTENSIONS, DETECT_OBJECTS_FILENAME,
    YOLO_MODEL_NAME, FRAME_SKIP, YOLO_THRESHOLD, TEMP_FOLDER, CONVERTED_VIDEO_SIZE,
    SAVE_STILLS, KEEP_VIDEOS_WITH_OBJECTS, DELETE_DRY_RUN,
    RECENT_FILES_MAX_SIZE_GB, HISTORICAL_FILES_MAX_SIZE_GB, FREE_SPACE_BUFFER_GB, FOLDER_SIZE_FILENAME
)
from lib.identify_camera_files_to_process import recursively_list_all_video_files_in_folder, filter_unprocessed_file_paths
from lib.analyse_camera_file import create_yolo_model, detect_objects_in_video_file
from lib.utils import setup_root_logger, log
import json


def get_folder_from_file_path(file_path):
    """Get the directory of a file path."""
    return os.path.dirname(file_path)

def is_camera_date_folder(folder_path):
    """Check if a folder path ends with yyyy/mm/dd format."""
    # Extract the last 3 parts of the path
    parts = folder_path.replace('\\', '/').split('/')
    if len(parts) < 3:
        return False

    year, month, day = parts[-3], parts[-2], parts[-1]

    # Check if they match yyyy/mm/dd pattern
    year_pattern = r'^\d{4}$'
    month_day_pattern = r'^(0[1-9]|1[0-2])$'  # 01-12
    day_pattern = r'^(0[1-9]|[12][0-9]|3[01])$'  # 01-31

    return (re.match(year_pattern, year) and
            re.match(month_day_pattern, month) and
            re.match(day_pattern, day))

def get_camera_folders_from_files(all_video_file_paths):
    """
    Extract unique camera folders (yyyy/mm/dd format) from video file paths.
    Returns a list of folder paths sorted in descending order (most recent first).
    """
    folders = set()
    for file_path in all_video_file_paths:
        folder = get_folder_from_file_path(file_path)
        if is_camera_date_folder(folder):
            folders.add(folder)

    # Sort descending (most recent first) - relies on yyyy/mm/dd string sorting
    return sorted(list(folders), reverse=True)

def calculate_folder_size(folder_path):
    """Calculate total size of all files in a folder in GB."""
    total_size = 0
    try:
        for entry in os.scandir(folder_path):
            if entry.is_file(follow_symlinks=False):
                try:
                    total_size += entry.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total_size / (1024**3)  # Convert to GB

def get_or_calculate_folder_size(folder_path, folder_size_filename):
    """
    Get folder size from cache file or calculate it.
    Returns size in GB.
    """
    cache_file = os.path.join(folder_path, folder_size_filename)

    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return float(f.read().strip())
        except (ValueError, OSError):
            pass

    # Calculate and cache
    size_gb = calculate_folder_size(folder_path)
    try:
        with open(cache_file, 'w') as f:
            f.write(f"{size_gb:.6f}")
    except OSError:
        log(f"Warning: Could not write cache file: {cache_file}")

    return size_gb

def update_folder_size_cache(folder_path, folder_size_filename):
    """Recalculate and update the folder size cache file."""
    size_gb = calculate_folder_size(folder_path)
    cache_file = os.path.join(folder_path, folder_size_filename)
    try:
        with open(cache_file, 'w') as f:
            f.write(f"{size_gb:.6f}")
    except OSError:
        log(f"Warning: Could not write cache file: {cache_file}")
    return size_gb

def get_video_files_in_folder(folder_path, video_file_extensions):
    """Get all video files in a specific folder (not recursive)."""
    video_files = []
    try:
        for entry in os.scandir(folder_path):
            if entry.is_file() and entry.name.lower().endswith(video_file_extensions):
                video_files.append(entry.path)
    except OSError:
        pass
    return video_files

def has_target_objects_in_video(file_path, detect_objects_filename, keep_videos_with_objects):
    """Check if a video file has detected target objects."""
    folder_path = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    detected_objects_file = os.path.join(folder_path, detect_objects_filename)

    if not os.path.exists(detected_objects_file):
        return False

    try:
        with open(detected_objects_file, 'r') as f:
            detected_data = json.load(f)
            if file_name in detected_data:
                detected_objects = set(detected_data[file_name])
                return bool(detected_objects.intersection(keep_videos_with_objects))
    except (json.JSONDecodeError, KeyError, OSError):
        pass

    return False

def remove_file_and_log(file_path, reason, dry_run):
    """Remove a file with logging."""
    if os.path.exists(file_path):
        if not dry_run:
            try:
                os.remove(file_path)
            except OSError as e:
                log(f"ERROR: Could not remove file {file_path}: {e}")
                return False
        log(f"[{reason}] Removed file: {file_path}")
        return True
    return False

def remove_folder_and_log(folder_path, reason, dry_run):
    """Remove an entire folder and all its contents with logging."""
    if os.path.exists(folder_path):
        if not dry_run:
            try:
                shutil.rmtree(folder_path)
            except OSError as e:
                log(f"ERROR: Could not remove folder {folder_path}: {e}")
                return False
        log(f"[{reason}] Removed folder and all contents: {folder_path}")
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
    - Calculating folder sizes (caching results)
    - Keeping recent folders (up to RECENT_FILES_MAX_SIZE_GB)
    - Removing non-target videos from folders that exceed the first threshold
    - Removing entire folders that exceed the second threshold
    """
    log("=" * 80)
    log("STEP 2 & 3: Managing disk space (folder-based approach)")
    log("=" * 80)

    # Get all camera folders sorted by date (most recent first)
    camera_folders = get_camera_folders_from_files(all_video_file_paths)
    log(f"Found {len(camera_folders)} camera date folders")

    # Step 1: Calculate/retrieve folder sizes
    log("Step 1: Calculating folder sizes...")
    folder_sizes = {}
    for idx, folder_path in enumerate(camera_folders, 1):
        size_gb = get_or_calculate_folder_size(folder_path, FOLDER_SIZE_FILENAME)
        folder_sizes[folder_path] = size_gb
        if idx % 100 == 0:
            log(f"  Processed {idx}/{len(camera_folders)} folders")

    log(f"Completed calculating sizes for {len(camera_folders)} folders")

    # Step 2: Identify phase 1 folders (recent, below first threshold)
    log(f"Step 2: Identifying Phase 1 folders (target: {RECENT_FILES_MAX_SIZE_GB} GB)")
    cumulative_size = 0.0
    phase1_end_index = 0

    for idx, folder_path in enumerate(camera_folders):
        cumulative_size += folder_sizes[folder_path]
        if cumulative_size >= RECENT_FILES_MAX_SIZE_GB:
            phase1_end_index = idx  # This folder exceeded threshold, it's NOT in phase 1
            break
        phase1_end_index = idx + 1  # All folders processed are in phase 1

    phase1_folders = camera_folders[:phase1_end_index]
    phase1_size = sum(folder_sizes[f] for f in phase1_folders)

    log(f"Phase 1 (recent, kept untouched): {len(phase1_folders)} folders, {phase1_size:.2f} GB")

    # Step 3: Process phase 2 folders (remove non-target videos)
    log(f"Step 3: Processing Phase 2 folders (remove videos without target objects)")
    phase2_start_index = phase1_end_index
    dirty_folders = set()
    removed_files_count = 0

    for idx in range(phase2_start_index, len(camera_folders)):
        folder_path = camera_folders[idx]
        video_files = get_video_files_in_folder(folder_path, VIDEO_FILE_EXTENSIONS)

        for video_file in video_files:
            if not has_target_objects_in_video(video_file, DETECT_OBJECTS_FILENAME, KEEP_VIDEOS_WITH_OBJECTS):
                if remove_file_and_log(video_file, "PHASE2_NO_TARGET", DELETE_DRY_RUN):
                    removed_files_count += 1
                    dirty_folders.add(folder_path)

    log(f"Removed {removed_files_count} videos without target objects from {len(dirty_folders)} folders")

    # Step 4: Recalculate sizes for dirty folders
    if dirty_folders:
        log(f"\nStep 4: Recalculating sizes for {len(dirty_folders)} modified folders")
        for folder_path in dirty_folders:
            new_size = update_folder_size_cache(folder_path, FOLDER_SIZE_FILENAME)
            folder_sizes[folder_path] = new_size

    # Step 5: Calculate cumulative size from phase 2 start to find where we exceed second threshold
    log(f"Step 5: Identifying folders to remove (beyond {RECENT_FILES_MAX_SIZE_GB + HISTORICAL_FILES_MAX_SIZE_GB} GB)")
    cumulative_from_phase2 = 0.0
    phase2_end_index = phase2_start_index

    for idx in range(phase2_start_index, len(camera_folders)):
        cumulative_from_phase2 += folder_sizes[camera_folders[idx]]
        if cumulative_from_phase2 >= HISTORICAL_FILES_MAX_SIZE_GB:
            phase2_end_index = idx  # Keep up to this folder
            break
        phase2_end_index = idx + 1

    phase2_folders = camera_folders[phase2_start_index:phase2_end_index]
    phase2_size = sum(folder_sizes[f] for f in phase2_folders)

    log(f"Phase 2 (historical with targets): {len(phase2_folders)} folders, {phase2_size:.2f} GB")

    # Step 6: Remove all remaining folders
    folders_to_remove = camera_folders[phase2_end_index:]
    log(f"Step 6: Removing {len(folders_to_remove)} folders beyond threshold")
    removed_folders_count = 0

    for folder_path in folders_to_remove:
        if remove_folder_and_log(folder_path, "PHASE3_OVER_LIMIT", DELETE_DRY_RUN):
            removed_folders_count += 1

    log(f"Removed {removed_folders_count} entire folders")

    # Summary
    log("=" * 80)
    log("DISK SPACE MANAGEMENT SUMMARY")
    log("=" * 80)
    log(f"Phase 1 (recent, all kept): {len(phase1_folders)} folders, {phase1_size:.2f} GB (target: {RECENT_FILES_MAX_SIZE_GB} GB)")
    log(f"Phase 2 (historical with targets): {len(phase2_folders)} folders, {phase2_size:.2f} GB (target: {HISTORICAL_FILES_MAX_SIZE_GB} GB)")
    log(f"Total kept: {len(phase1_folders) + len(phase2_folders)} folders, {phase1_size + phase2_size:.2f} GB")
    log(f"Removed: {removed_files_count} individual files + {removed_folders_count} entire folders")
    log(f"Expected free space increase: ~{sum(folder_sizes[f] for f in folders_to_remove):.2f} GB")

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
    setup_root_logger(
        with_logfile=True,
        log_folder_path="../logs/",
        log_file_name="daily_workflow.log",
        timestamp_log_file=True
    )
    run_daily_workflow()




