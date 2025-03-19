# Stage 1: Install dependencies
FROM python:3.9 AS dependencies

# Copy requirement-file to the container
COPY warehouse/requirements.txt /app/requirements.txt

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Copy Python code
FROM dependencies

# Copy rest of the application to the container
COPY warehouse/ /app

# Set working directory
WORKDIR /app

# Run the application
CMD ["python", "master_consumer.py"]
