ROOT_CAMERA_FOLDER_PATH = "../data/demo_clips"
FORCE_REEVALUATION = False # if True, will re-evaluate all video files even if detected_objects.json already exists
VIDEO_FILE_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv') # video file extensions to consider
TEMP_FOLDER = "../data/temp" # location to store intermediate working video files
CONVERTED_VIDEO_SIZE=480 # horizontal resolution of the intermediate working video file (1080 = HD, 720 = HD ready, 480 = SD)
YOLO_MODEL_NAME = "yolov8n.pt"  # n/s/m/l/x
YOLO_THRESHOLD = 0.3 # 0.2-0.3 for caputuring all predictions, 0.4-0.5 for general use, 0.6-0.7 for high precision
FRAME_SKIP = 10 # amount of frames per single evaluation
SAVE_STILLS = True
DETECT_OBJECTS_FILENAME="detected_objects.json"
DELETE_DRY_RUN = True # if True, will only log files that would be deleted, but not actually delete them
KEEP_VIDEOS_WITH_OBJECTS = {"person"} # define as a set
