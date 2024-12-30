import json
import threading
import time

from kafka import KafkaConsumer
from kafka.errors import KafkaTimeoutError


class ValidationThread(threading.Thread):
    def __init__(self, kafka_servers, kafka_topic, msg_callback=None, timeout_s=999999):
        super().__init__()
        self.msg_ids = None  # Make sure the ids are strings
        self.kafka_servers = kafka_servers
        self.msg_callback = msg_callback
        self.timeout_s = timeout_s
        self.received_ids = set()
        self.duplicates = 0
        self.unknowns = 0
        self.errors = 0
        self.running = True
        self.topic = kafka_topic
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=kafka_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            session_timeout_ms=10000,
            request_timeout_ms=30000,
            heartbeat_interval_ms=3000,
            group_id='my-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

    def wait_for_msg_ids(self, msg_ids, timeout_s=10):
        self.msg_ids = set(str(x) for x in msg_ids)  # Make sure the ids are strings
        self.timeout_s = timeout_s
        if self.get_num_msg_remaining() == 0:
            print(f"Successfully received all {len(self.msg_ids)} messages! "
                  f"(duplicates: {self.duplicates}, unknowns: {self.unknowns})")
            self.running = False
        else:
            print(f"Waiting for {len(self.msg_ids)} messages with timeout {timeout_s} seconds")
        self.join()
        return len(self.received_ids)

    def run(self):
        print(f"Starting message consumption from topic {self.topic}")
        prev_msg_received_time = time.time()

        while self.running:
            if time.time() - prev_msg_received_time > self.timeout_s:
                print(f"Watchdog timed out! (exceeded {self.timeout_s} seconds)")
                self.print_stats()
                self.running = False
                break

            poll_timeout_seconds = 5
            try:
                messages = self.consumer.poll(timeout_ms=poll_timeout_seconds * 1000)
            except KafkaTimeoutError:
                print(f"KafkaTimeoutError! (exceeded {poll_timeout_seconds} seconds)")
                # self.print_stats()
                # self.running = False
                break

            if not messages:
                continue

            for tp, msgs in messages.items():
                for message in msgs:
                    if len(message.value) == 0:
                        continue
                    try:
                        msg_id = message.value['id']
                    except KeyError:
                        print(f"Message ID not included in Kafka message! (error count: {self.errors})")
                        self.errors += 1
                        continue
                    if self.msg_callback is not None:
                        self.msg_callback(message.value)
                    if msg_id in self.received_ids:
                        print(
                            f"WARNING: Received duplicate of ID: {msg_id} with timestamp: {message.value['timestamps']}")
                        self.duplicates += 1
                    elif self.msg_ids is not None and msg_id not in self.msg_ids:
                        print(f"WARNING: Received unknown ID: {msg_id} with timestamp: {message.value['timestamps']}")
                        self.unknowns += 1
                    else:
                        self.received_ids.add(msg_id)
                        self.print_sparse_message(
                            f"Received message {message.value['id']} with timestamp: {message.value['timestamps']}, ({self.get_num_msg_remaining()} remaining)"
                        )
                    if self.get_num_msg_remaining() == 0:
                        print(
                            f"Successfully received all {len(self.msg_ids)} messages! (duplicates: {self.duplicates}, unknowns: {self.unknowns})"
                        )
                        self.running = False
            prev_msg_received_time = time.time()

        self.consumer.close()

    def get_num_msg_remaining(self):
        """
        How many messages are still expected to be received?

        This is None if the msg_ids are not set yet.
        """
        if self.msg_ids is None:
            return None
        return len(self.msg_ids) - len(self.received_ids)

    def print_sparse_message(self, msg):
        """Only print some messages to keep the output clean"""
        remaining = self.get_num_msg_remaining()
        if len(self.received_ids) % 100 == 0 or (remaining != None and self.get_num_msg_remaining() < 10):
            print(msg)

    def print_stats(self):
        print(f"Messages received: {self.received_ids}")
        print(f"Messages missing: {len(self.msg_ids - self.received_ids)}")
        print(f"Duplicates: {self.duplicates}, errors: {self.errors}")

if __name__ == '__main__':
    kafka_servers = ['localhost:10001', 'localhost:10002', 'localhost:10003']
    kafka_topic = 'test-topic'

    # Define a callback function
    def msg_callback(msg):
        print(f"Callback received message: {msg}")

    # Create a new ValidationThread instance
    consumer_thread = ValidationThread(
        kafka_servers=kafka_servers,
        kafka_topic=kafka_topic,
        msg_callback=msg_callback
    )

    # Simulate message IDs for testing
    test_msg_ids = [str(x) for x in range(100)]

    # Start consumer thread and wait for messages
    consumer_thread.wait_for_msg_ids(test_msg_ids, timeout_s=20)

    print("Finished message consumption.")
