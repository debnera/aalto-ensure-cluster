FROM python:3.8

# SET WORKDIT & CLONE OVER NECESSARI FILES
COPY ./app /app
#COPY ./requirements.txt /app/requirements.txt
WORKDIR /app

# INSTALL DEPENDENCIES
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 wget -y
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# DOWNLOAD & SET YOLO ZIP
RUN mkdir -p /root/.cache/torch/hub/
RUN wget -O /root/.cache/torch/hub/master.zip https://github.com/ultralytics/yolov5/zipball/master

# RUN CONSUMER
CMD ["python", "processor.py"]

# docker build --no-cache -t workload_consumer -f consumer.Dockerfile .
# docker run workload_consumer

# docker tag workload_consumer:latest wickstjo/workload_consumer:latest
# docker push wickstjo/workload_consumer:latest