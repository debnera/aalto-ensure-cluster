import json
from kafka import KafkaConsumer

# Configure the Kafka consumer
def wait_for_results(image_ids):
    kafka_servers = 'localhost:10001,localhost:10002,localhost:10003'
    consumer = KafkaConsumer(
        'yolo_output',
        bootstrap_servers=kafka_servers,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='my-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    print(f"Sent image IDs: {image_ids}")
    print("Waiting for messages from 'yolo_output'...")

    received_ids = set()
    duplicates = 0
    unknowns = 0
    errors = 0
    for message in consumer:
        if len(message.value) == 0:
            break
        try:
            img_id = message.value['id']
        except:
            print(f"Image id not included in kafka message! (error count: {errors})")
            errors += 1
            continue
        if img_id in received_ids:
            # Should never go here
            print(f"WARNING: Received duplicate of id: {img_id} with timestamp: {message.value['timestamps']}")
            duplicates += 1
        if img_id not in image_ids:
            print(f"WARNING: Received unknown id: {img_id} with timestamp: {message.value['timestamps']}")
            unknowns += 1
        else:
            received_ids.add(img_id)
            print(f"Received message {message.value['id']} with timestamp: {message.value['timestamps']}")
        if len(received_ids) == len(image_ids):
            print(f"Successfully received all {len(image_ids)} messages! (duplicates: {duplicates}, unknowns: {unknowns})")

    consumer.close()

if __name__ == '__main__':
    wait_for_results(image_ids=[x for x in range(100)])
