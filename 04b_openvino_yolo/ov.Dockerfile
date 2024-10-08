# Stage 1: Install dependencies
FROM python:3.8 AS dependencies

# Copy requirement-file to the container
COPY ./app/requirements.txt /app/requirements.txt

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update
RUN apt-get install -y ffmpeg libsm6 libxext6 wget
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Copy Python code
FROM dependencies

# Copy rest of the application to the container
COPY ./app /app

# Set working directory
WORKDIR /app

# Run the application
CMD ["python", "vino_consumer.py"]