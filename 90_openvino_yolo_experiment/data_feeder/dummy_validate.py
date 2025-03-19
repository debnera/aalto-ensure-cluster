import json
import time

from kafka import KafkaConsumer
from kafka.errors import KafkaTimeoutError



# Configure the Kafka consumer
def wait_for_results(image_ids, kafka_servers, msg_callback=None, timeout_s=10):

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
    print(f"Waiting for {len(image_ids)} images")

    received_ids = set()
    def get_num_msg_remaining():
        """ How many msg are we still expecting to receive? """
        return len(image_ids) - len(received_ids)
    def print_sparse(msg):
        """ Only print some messages to keep the output clean """
        if get_num_msg_remaining() % 100 == 0 or get_num_msg_remaining() < 10:
            print(msg)


    duplicates = 0
    unknowns = 0
    errors = 0
    running = True
    prev_msg_received_time = time.time()
    while running:
        # Poll for new messages
        if time.time() - prev_msg_received_time > timeout_s:
            print(f"Watchdog timed out! (exceeded {timeout_s} seconds)")
            print(f"Messages received: {received_ids}")
            print(f"Messages missing: {len(image_ids - received_ids)}")
            print(f"Duplicates: {duplicates}, errors: {errors}")
            running = False
            break

        try:
            messages = consumer.poll(timeout_ms=timeout_s*1000)
        except KafkaTimeoutError:
            print(f"KafkaTimeoutError! (exceeded {timeout_s} seconds)")
            print(f"Messages received: {received_ids}")
            print(f"Messages missing: {len(image_ids - received_ids)}")
            print(f"Duplicates: {duplicates}, errors: {errors}")
            running = False
            break

        if not messages:
            continue

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
                    remaining = get_num_msg_remaining()
                    print_sparse(f"Received message {message.value['id']} with timestamp: {message.value['timestamps']}, ({remaining} remaining)")
                if get_num_msg_remaining() == 0:
                    print(
                        f"Successfully received all {len(image_ids)} messages! (duplicates: {duplicates}, unknowns: {unknowns})")
                    running = False
        prev_msg_received_time = time.time()

    consumer.close()
    return len(received_ids)

if __name__ == '__main__':
    kafka_servers = 'localhost:10001,localhost:10002,localhost:10003'
    wait_for_results(image_ids=[x for x in range(100)], kafka_servers=kafka_servers)
