FROM python:3.8.18 as base
LABEL authors="anton"
ADD requirements.txt .
RUN pip install -r requirements.txt

FROM base
ADD utilz ./utilz
ADD validate_to_csv.py .
ENTRYPOINT ["python", "./validate_to_csv.py"]