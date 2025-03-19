def zip_snapshot(snapshot_path, qos_csv_folder=None, name="zip_snapshot_test", log_func=print, delete_original=True):
    import os
    import zipfile
    import shutil
    import time
    import subprocess

    start_zip_time = time.time()

    # Ensure qos_csv_folder is a list
    if qos_csv_folder is None:
        qos_csv_folder = []
    elif isinstance(qos_csv_folder, str):
        qos_csv_folder = [qos_csv_folder]

    # Copy qos CSVs from multiple folders
    for idx, folder in enumerate(qos_csv_folder):
        if folder is not None:
            # Check if the folder exists
            if not os.path.exists(folder) or not os.path.isdir(folder):
                log_func(f"Error: QoS folder '{folder}' does not exist or is not a directory. Skipping.")
                continue

            # Create a unique destination folder for each input folder
            destination_qos_folder = os.path.join(snapshot_path, f"qos_outputs_{idx}")
            try:
                shutil.copytree(folder, destination_qos_folder)
                log_func(f"Copied warehouse CSV files from {folder} to {destination_qos_folder}")
            except Exception as e:
                log_func(f"Error copying files from {folder} to {destination_qos_folder}: {e}")

    # Copying the current script and its configurations to the snapshot
    current_script_path = __file__  # Path to the current script
    script_destination = os.path.join(snapshot_path, os.path.basename(current_script_path))
    try:
        shutil.copy2(current_script_path, script_destination)
        log_func(f"Copied current script to {script_destination}")
    except Exception as e:
        log_func(f"Error copying current script to {script_destination}: {e}")

    # Extracting git commit and date
    try:
        result = subprocess.run(["git", "log", "-1", "--pretty=format:%H %ad"], capture_output=True, text=True)
        git_commit_info = result.stdout.strip()
        git_info_path = os.path.join(snapshot_path, "git_commit_info.txt")
        with open(git_info_path, "w") as git_info_file:
            git_info_file.write(git_commit_info)
        log_func(f"Copied git commit info to {git_info_path}")
    except Exception as e:
        log_func(f"Error retrieving git commit info: {e}")

    # Create a zip file from the snapshot_path
    zip_filename = f"{int(start_zip_time)}_{name}.zip"
    zip_filepath = os.path.join(os.path.dirname(snapshot_path), zip_filename)
    try:
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(snapshot_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, snapshot_path)
                    zipf.write(file_path, arcname)
    except Exception as e:
        log_func(f"Error creating zip file: {e}")

    end_zip_time = time.time()
    zip_duration = end_zip_time - start_zip_time
    zip_size = os.path.getsize(zip_filepath)

    # Optionally delete the original files
    if delete_original:
        try:
            shutil.rmtree(snapshot_path)
            for folder in qos_csv_folder:
                if folder is not None and os.path.exists(folder) and os.path.isdir(folder):
                    shutil.rmtree(folder)
            log_func(f"Deleted original files in {snapshot_path} and provided QoS folders")
        except Exception as e:
            log_func(f"Error deleting original files: {e}")

    # Log the details
    log_func(f"Zipping completed in {zip_duration:.2f} seconds")
    log_func(f"Zip file size: {zip_size / (1024 * 1024):.2f} MB")
    log_func(f"Zip file path: {zip_filepath}")


if __name__ == "__main__":
    snap_path = r"C:\Users\Anton\Documents\projektit\05_ensure\aalto-ensure-cluster\91_warehouse_experiment\local_kube_kafka"
    qos_path = r"C:\Users\Anton\Documents\projektit\05_ensure\aalto-ensure-cluster\91_warehouse_experiment\qos_outputs\1735566156.847868_(6.10000)"
    zip_snapshot(snap_path, qos_path, delete_original=False)
