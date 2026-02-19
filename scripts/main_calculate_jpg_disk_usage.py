# calculate disk space used by JPG files under ROOT FOLDER (recursively, so also nested subfolders)

import os

ROOT_FOLDER = r"T:\ftp_reolink\reolink"

def calculate_jpg_disk_usage(root_folder):
    total_size_bytes = 0
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower().endswith('.jpg'):
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size_bytes += os.path.getsize(file_path)
                except OSError:
                    pass
    total_size_gb = total_size_bytes / (1024 ** 3)
    return total_size_gb

if __name__ == "__main__":
    jpg_disk_usage_gb = calculate_jpg_disk_usage(ROOT_FOLDER)
    print(f"Total disk usage by JPG files under {ROOT_FOLDER}: {jpg_disk_usage_gb:.2f} GB")