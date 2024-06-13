from prometheus_client import Counter, Histogram, start_http_server
import time

# Create metrics
job_count = Counter('yolo_requests_received', 'Number of received jobs')
job_processing_time = Histogram('yolo_inference_time', 'Job processing time in seconds')

def process_job():
    # Simulate job processing
    time.sleep(0.5)
    job_count.inc()
    job_processing_time.observe(0.5)

if __name__ == '__main__':
    # Start the Prometheus HTTP server
    start_http_server(8000)

    # Simulate receiving jobs
    while True:
        process_job()
