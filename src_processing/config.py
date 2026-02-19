ROOT_CAMERA_FOLDER_PATH = r"T:\ftp_reolink\reolink"
FORCE_REEVALUATION = False # if True, will re-evaluate all video files even if detected_objects.json already exists
VIDEO_FILE_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv') # video file extensions to consider
TEMP_FOLDER = "../data/temp" # location to store intermediate working video files
CONVERTED_VIDEO_SIZE=480 # horizontal resolution of the intermediate working video file (1080 = HD, 720 = HD ready, 480 = SD)
YOLO_MODEL_NAME = "models/yolov8n.pt"  # n/s/m/l/x
YOLO_THRESHOLD = 0.3 # 0.2-0.3 for caputuring all predictions, 0.4-0.5 for general use, 0.6-0.7 for high precision
FRAME_SKIP = 10 # amount of frames per single evaluation
SAVE_STILLS = True
DETECT_OBJECTS_FILENAME="detected_objects.json"
FOLDER_SIZE_FILENAME="this_folder_size.txt"
DELETE_DRY_RUN = False # if True, will only log files that would be deleted, but not actually delete them
KEEP_VIDEOS_WITH_OBJECTS = {"person"} # define as a set
RECENT_FILES_MAX_SIZE_GB = 500  # Keep the most recent X GB of files untouched (regardless of content)
HISTORICAL_FILES_MAX_SIZE_GB = 400  # Keep older files with target objects, capped at X GB
FREE_SPACE_BUFFER_GB = 30  # Expected free space remaining (e.g., 930GB - 500GB - 400GB = 30GB)

