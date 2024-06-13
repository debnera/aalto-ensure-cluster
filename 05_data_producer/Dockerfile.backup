FROM python:3.8.18 as base
LABEL authors="anton"
ADD requirements.txt .
RUN pip install -r requirements.txt

FROM base
ADD yolo_mockup.py .
ENTRYPOINT ["python", "./yolo_mockup.py"]