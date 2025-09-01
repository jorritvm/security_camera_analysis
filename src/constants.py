ROOT_CAMERA_FOLDER_PATH = "../data/demo_clips"
TEMP_FOLDER = "../data/temp" # location to store intermediate working video files
CONVERTED_VIDEO_SIZE=1280 # size of the intermediate working video file
YOLO_MODEL_NAME = "yolov8s.pt"  # n/s/m/l/x
YOLO_THRESHOLD = 0.3 # 0.2-0.3 for caputuring all predictions, 0.4-0.5 for general use, 0.6-0.7 for high precision
FRAME_SKIP = 3 # amount of frames per single evaluation
DETECT_OBJECTS_FILENAME="detected_objects.json"
