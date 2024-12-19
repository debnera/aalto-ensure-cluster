import os
import requests

points = [1000, 5000, 10000]
robots = [1, 2, 4, 6]

# Ensure 'datasets' folder exists
os.makedirs("datasets", exist_ok=True)

for robot in robots:
    for point in points:
        url = f"https://github.com/Aalto-ESG/fog-iot-2020-data/raw/master/robots-{robot}/points-per-frame-{point}.hdf5"
        file_name = f"datasets/robots-{robot}_points-{point}.hdf5"
        
        # Check if the file already exists
        if not os.path.exists(file_name):
            print(f"Downloading {file_name}...")
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_name, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        f.write(chunk)
            else:
                print(f"Failed to download {url}. Status code: {response.status_code}")
        else:
            print(f"File {file_name} already exists. Skipping download.")