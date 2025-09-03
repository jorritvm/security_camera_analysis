"""
Entrypoint module to benchmark YOLO model performance so we can define the proper settings for production
The resulting optimized constants will be set up in config.py
"""
import os
from identify_camera_files_to_process import recursively_list_all_video_files_in_folder, convert_list_of_file_paths_to_dict
from analyse_camera_file import detect_objects_in_video_files
from config import VIDEO_FILE_EXTENSIONS, TEMP_FOLDER, YOLO_MODEL_NAME, YOLO_THRESHOLD
from utils import Timer


results = dict() # key = (json_filename), value = (elapsed_seconds, acc, prec, fpr)


def run_campaign():
    """Run a series of benchmarks with different settings and store the results"""

    # files to use in the benchmark are ALL files in the demo folder, every time again
    folder_path = "../data/demo_clips"
    file_paths = recursively_list_all_video_files_in_folder(folder_path=folder_path,
                                                            extensions=VIDEO_FILE_EXTENSIONS)

    # define different settings to benchmark
    # change vsize
    run_single_benchmark(file_paths, 1080, "yolov8s.pt", 1, "bench_1080p_small_f1.json")
    run_single_benchmark(file_paths, 720, "yolov8s.pt", 1, "bench_720p_small_f1.json")
    run_single_benchmark(file_paths, 480, "yolov8s.pt", 1, "bench_480p_small_f1.json")
    # change model
    run_single_benchmark(file_paths, 1080, "yolov8n.pt", 1, "bench_1080p_nano_f1.json")
    run_single_benchmark(file_paths, 720, "yolov8n.pt", 1, "bench_720p_nano_f1.json")
    run_single_benchmark(file_paths, 480, "yolov8n.pt", 1, "bench_480p_nano_f1.json")
    # change frame skip
    run_single_benchmark(file_paths, 1080, "yolov8s.pt", 3, "bench_1080p_small_f3.json")
    run_single_benchmark(file_paths, 1080, "yolov8s.pt", 10, "bench_1080p_small_f10.json")
    run_single_benchmark(file_paths, 1080, "yolov8s.pt", 30, "bench_1080p_small_f30.json")
    run_single_benchmark(file_paths, 480, "yolov8s.pt", 3, "bench_480p_small_f3.json")
    run_single_benchmark(file_paths, 480, "yolov8s.pt", 10, "bench_480p_small_f10.json")
    run_single_benchmark(file_paths, 480, "yolov8s.pt", 30, "bench_480p_small_f30.json")

    print("------------------ benchmark results ------------------")
    # print to console
    print(results)
    # write to file
    output_file_path = os.path.join(folder_path, "benchmark_results.json")
    with open(output_file_path, "w") as f:
        import json
        json.dump(results, f, indent=4)
    print("wrote benchmark results to file: " + output_file_path)


def run_single_benchmark(file_paths, vsize, yolo_model, frame_skip, json_filename):
    """Run a single benchmark with the given settings and store the results"""

    print("starting benchmark with description: " + json_filename)

    # execute the video file analysis
    timer = Timer("Total processing time")
    timer.start()
    all_detected_objects = detect_objects_in_video_files(file_paths , TEMP_FOLDER, vsize, yolo_model,
                                                         YOLO_THRESHOLD, frame_skip, json_filename)
    timer.stop()
    elapsed_seconds = timer.end_time - timer.start_time
    print("elapsed seconds: " + str(elapsed_seconds))

    # evaluate the results
    acc, prec, fpr = establish_metrics(all_detected_objects)

    results[json_filename] = (elapsed_seconds, acc, prec, fpr)


def establish_metrics(all_detected_objects) -> (float, float, float):
    """Calculates accuracy, precision and false positive rate based on the detected objects"""
    correct_classifications = 0
    total_classifications = 0
    true_positives = 0
    false_positives = 0
    true_negatives = 0
    for key, value in all_detected_objects.items():
        total_classifications += 1
        basename = os.path.basename(key)
        should_have_person = False
        if "human" in basename:
            should_have_person = True
        actually_has_person = False
        if "person" in value:
            actually_has_person = True

        if should_have_person == actually_has_person:
            correct_classifications += 1

        if actually_has_person and not should_have_person:
            false_positives += 1

        if not actually_has_person and not should_have_person:
            true_negatives += 1

        if actually_has_person and should_have_person:
            true_positives += 1

    accuracy = correct_classifications / total_classifications
    precision = true_positives / (true_positives + false_positives)
    false_positive_rate = false_positives / (false_positives + true_negatives)

    return accuracy, precision, false_positive_rate


if __name__ == '__main__':
    run_campaign()