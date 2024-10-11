import os

from ultralytics import YOLO

# Change dir to avoid spamming cwd with all sorts of files
output_folder = "model_cache"
os.makedirs(output_folder, exist_ok=True)
os.chdir(output_folder)

# List all models to download
models = []
models += ["yolo11n", "yolo11s", "yolo11m", "yolo11l", "yolo11x"] # YOLO v11 released on v8.3.0 (2024-09-29)
models += ["yolov10n", "yolov10s", "yolov10m", "yolov10l", "yolov10x"]
models += ["yolov9t", "yolov9s", "yolov9m", "yolov9c", "yolov9e"]  # NOTE: Different naming on v9 models
models += ["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"]

missing_models = []

for model in models:
    if not os.path.exists(f"{model}.pt"):
        missing_models.append(model)

# Print missing models before download
print("Missing models before download:", missing_models)

for model in missing_models:
    # Download missing models
    yolo_ultralytics = YOLO(f"{model}.pt")
    # pass

# Listing missing models again to confirm download
post_download_missing_models = [model for model in models if not os.path.exists(f"{model}.pt")]
print("Missing models after download:", post_download_missing_models)
