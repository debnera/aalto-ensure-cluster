def zip_snapshot(snapshot_path, yolo_csv_folder, name="yolov8n", log_func=print):
    import os
    import zipfile
    import shutil
    start_zip_time = time.time()
    # Copy yolo CSVs
    if yolo_csv_folder is not None:
        # Copy contents from yolo_csv_folder to snapshot_path
        destination_yolo_folder = os.path.join(snapshot_path, "yolo_outputs")
        shutil.copytree(yolo_csv_folder, destination_yolo_folder)
        log(f"Copied warehouse CSV files from {yolo_csv_folder} to {destination_yolo_folder}")
    # Copying the current script and its configurations to the snapshot
    current_script_path = __file__  # Path to the current script
    script_destination = os.path.join(snapshot_path, os.path.basename(current_script_path))
    shutil.copy2(current_script_path, script_destination)
    log(f"Copied current script to {script_destination}")
    # Extracting git commit and date
    result = subprocess.run(["git", "log", "-1", "--pretty=format:%H %ad"], capture_output=True, text=True)
    git_commit_info = result.stdout.strip()
    git_info_path = os.path.join(snapshot_path, "git_commit_info.txt")
    with open(git_info_path, "w") as git_info_file:
        git_info_file.write(git_commit_info)
    log(f"Copied git commit info to {git_info_path}")
    # Create a zip file from the snapshot_path
    zip_filename = f"{int(start_zip_time)}_{name}.zip"
    zip_filepath = os.path.join(os.path.dirname(snapshot_path), zip_filename)
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(snapshot_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, snapshot_path)
                zipf.write(file_path, arcname)
    end_zip_time = time.time()
    zip_duration = end_zip_time - start_zip_time
    zip_size = os.path.getsize(zip_filepath)
    # Optionally delete the original files
    delete_original = True  # Set this to False if you do not want to delete
    if delete_original:
        shutil.rmtree(snapshot_path)
        if yolo_csv_folder is not None:
            shutil.rmtree(yolo_csv_folder)
        log(f"Deleting original files in {snapshot_path} and {yolo_csv_folder}")
    # Log the details
    log(f"Zipping completed in {zip_duration:.2f} seconds")
    log(f"Zip file size: {zip_size / (1024 * 1024):.2f} MB")
    log(f"Zip file path: {zip_filepath}")