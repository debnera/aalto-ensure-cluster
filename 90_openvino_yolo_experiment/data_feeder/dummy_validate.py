import json
import time

from kafka import KafkaConsumer
from kafka.errors import KafkaTimeoutError


# Configure the Kafka consumer
def wait_for_results(image_ids, msg_callback=None, timeout_s=10):
    kafka_servers = 'localhost:10001,localhost:10002,localhost:10003'
    consumer = KafkaConsumer(
        'yolo_output',
        bootstrap_servers=kafka_servers,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        session_timeout_ms=10000,
        request_timeout_ms=30000,
        heartbeat_interval_ms=3000,
        group_id='my-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    image_ids = set(str(x) for x in image_ids)  # Make sure the ids are strings, as kafka gives them as strings
    print(f"Sent image IDs: {image_ids}")
    print("Waiting for messages from 'yolo_output'...")

    received_ids = set()
    duplicates = 0
    unknowns = 0
    errors = 0
    running = True
    prev_msg_received_time = time.time()
    while running:
        # Poll for new messages
        if time.time() - prev_msg_received_time > timeout_s:
            print(f"Timed out! (exceeded {timeout_s} seconds)")
            print(f"Messages received: {received_ids}")
            print(f"Messages missing: {len(image_ids - received_ids)}")
            print(f"Duplicates: {duplicates}, errors: {errors}")
            running = False
            break

        try:
            messages = consumer.poll(timeout_ms=timeout_s*1000)
        except KafkaTimeoutError:
            print(f"Timed out! (exceeded {timeout_s} seconds)")
            print(f"Messages received: {received_ids}")
            print(f"Messages missing: {len(image_ids - received_ids)}")
            print(f"Duplicates: {duplicates}, errors: {errors}")
            running = False
            break

        if not messages:
            continue
        prev_msg_received_time = time.time()
        for tp, msgs in messages.items():
            for message in msgs:
                if len(message.value) == 0:
                    continue
                try:
                    img_id = message.value['id']
                except:
                    print(f"Image id not included in kafka message! (error count: {errors})")
                    errors += 1
                    continue
                if msg_callback is not None:
                    msg_callback(message.value)
                if img_id in received_ids:
                    # Should never go here
                    print(f"WARNING: Received duplicate of id: {img_id} with timestamp: {message.value['timestamps']}")
                    duplicates += 1
                if img_id not in image_ids:
                    print(f"WARNING: Received unknown id: {img_id} with timestamp: {message.value['timestamps']}")
                    unknowns += 1
                else:
                    received_ids.add(img_id)
                    remaining = len(image_ids) - len(received_ids)
                    print(f"Received message {message.value['id']} with timestamp: {message.value['timestamps']}, ({remaining} remaining)")
                if len(received_ids) == len(image_ids):
                    print(
                        f"Successfully received all {len(image_ids)} messages! (duplicates: {duplicates}, unknowns: {unknowns})")
                    running = False

    consumer.close()
    return len(received_ids)

if __name__ == '__main__':
    wait_for_results(image_ids=[x for x in range(100)])
