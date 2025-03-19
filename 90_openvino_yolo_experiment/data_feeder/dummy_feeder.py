import json

from kafka import KafkaProducer
import numpy as np
import cv2
import itertools
import time

def feed_data(n_images=100, kafka_servers='localhost:10001,localhost:10002,localhost:10003'):
    # Configure the Kafka producer
    producer = KafkaProducer(bootstrap_servers=kafka_servers)

    # Send the image to Kafka
    use_jpg = True
    image_ids = set()
    image_count = itertools.count()
    for i in range(n_images):
        # Send the image to Kafka with image id as the key

        # Generate random RGB image
        image_size = (640, 640, 3)
        image = np.random.randint(0, 256, image_size, dtype=np.uint8)

        # Encode the image as a byte array
        if use_jpg:
            # Cuts image size by over 60 %
            _, buffer = cv2.imencode('.jpg', image)
            img_as_bytes = buffer.tobytes()
        else:
            img_as_bytes = image.tobytes()

        # Send the image to Kafka as bytes
        image_id = next(image_count)
        producer.send('yolo_input', key=str(image_id).encode('utf-8'), value=img_as_bytes)
        image_ids.add(str(i))
        # producer.send('yolo_input', value=img_as_bytes)

        producer.flush()
        print(f"Sent image {i} to Kafka, {len(img_as_bytes)} bytes")
        # time.sleep(0.5)  # to simulate some delay between sends

    # Close the producer
    producer.close()
    return next(image_count)

if __name__ == '__main__':
    feed_data()
