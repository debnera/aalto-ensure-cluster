import json
from threading import Thread

from confluent_kafka.admin import AdminClient, NewTopic, NewPartitions
from confluent_kafka import TopicPartition


from .utils.kafka_utils import create_producer, create_consumer
from .utils.misc import create_lock

import time


def recreate_topic(kafka_servers, topic_name, num_partitions=5, replication_factor=1, log_func=print):
    """
    Always recreate the given Kafka topic to ensure a clean slate.
    Deletes the topic if it already exists, and waits for deletion before recreating it.
    Verifies that the topic was successfully created.

    Args:
        kafka_servers (str): Kafka bootstrap servers.
        topic_name (str): The name of the topic to create.
        num_partitions (int): Number of partitions for the topic.
        replication_factor (int): Replication factor for the topic.
        log_func (func): Logging function to use for output.
    """
    admin_client = AdminClient({'bootstrap.servers': kafka_servers})

    def wait_for_topic_deletion(admin_client, topic_name, timeout=60, log_func=print):
        """Wait for topic deletion to complete."""
        log_func(f"INFO: Waiting for topic {topic_name} to be deleted...")
        start = time.time()
        while time.time() - start < timeout:
            topics = admin_client.list_topics(timeout=5).topics
            if topic_name not in topics:
                log_func(f"INFO: Topic {topic_name} deleted successfully.")
                return True
            time.sleep(2)  # Poll every 2 seconds
        log_func(f"WARNING: Topic {topic_name} still exists after waiting for deletion!")
        return False

    try:
        # DELETE the topic if it exists
        existing_topics = admin_client.list_topics(timeout=10).topics
        if topic_name in existing_topics:
            log_func(f"INFO: Topic {topic_name} exists, deleting it...")
            fs = admin_client.delete_topics([topic_name])
            for topic, f in fs.items():
                try:
                    f.result()  # Wait for operation to finish
                except Exception as e:
                    log_func(f"ERROR: Failed to delete topic {topic}: {e}")
            if not wait_for_topic_deletion(admin_client, topic_name, timeout=60, log_func=log_func):
                log_func(f"ERROR: Could not delete topic {topic_name} completely! Aborting...")
                return

        # Refresh metadata to ensure topic list is consistent
        admin_client.poll(timeout=1)

        # CREATE the topic
        log_func(
            f"INFO: Creating topic {topic_name} with {num_partitions} partitions and replication factor {replication_factor}.")
        admin_client.create_topics(new_topics=[
            NewTopic(topic=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)
        ])

        # VERIFY the topic creation
        log_func(f"INFO: Verifying topic {topic_name} creation...")
        start = time.time()
        topic_created = False
        while time.time() - start < 10:  # Allow up to 10 seconds for the topic to appear
            topics = admin_client.list_topics(timeout=5).topics
            if topic_name in topics:
                log_func(f"INFO: Topic {topic_name} created successfully.")
                topic_created = True
                break
            time.sleep(2)  # Poll every 2 seconds
        if not topic_created:
            log_func(f"ERROR: Topic {topic_name} was not found after creation!")

    except Exception as e:
        log_func(f"ERROR: Failed to recreate topic {topic_name}: {e}")





# PARSE PYTHON ARGUMENTS
def init_kafka(kafka_servers, topic_name, num_partitions=5, log_func=print):
    """
    Try to initialize kafka topics, so consumers and others do not complain about missing topics.

    Num_partitions should at minimum be equivalent to the total number of consumers in the cluster.
    """

    log_func(f"INIT KAFKA TOPIC: {topic_name}, NUM PARTITIONS: {num_partitions}")
    admin_client = AdminClient({
        'bootstrap.servers': kafka_servers,
    })

    # CHECK WHAT TOPICS EXIST
    def query_topics():
        container = {}

        for name, parts in admin_client.list_topics().topics.items():
            container[name] = len(parts.partitions)

        # log_func(json.dumps(container, indent=4))
        return container

    # CREATE TOPICS WITH N PARTITIONS OR ADJUST IF EXISTS
    def create_topic(name, partitions, replication):

        # CHECK CURRENT TOPICS
        topic_data = query_topics()

        # ADJUST PARTITIONS IF TOPIC ALREADY EXISTS
        if name in topic_data:
            current_partitions = topic_data[name]
            log_func(f"INFO: TOPIC ({name}) HAS {current_partitions} PARTITIONS, TARGETING {partitions} PARTITIONS")
            if current_partitions < partitions:
                admin_client.create_partitions(
                    [NewPartitions(name, partitions)]
                )
                log_func(f"INFO: TOPIC ({name}) PARTITIONS UPDATED FROM {current_partitions} TO {partitions}")
            else:
                log_func(f"INFO: TOPIC ({name}) ALREADY EXISTS WITH {current_partitions} PARTITIONS")
            return

        # OTHERWISE, CREATE IT
        admin_client.create_topics(
            new_topics=[NewTopic(
                topic=name,
                num_partitions=partitions,
                replication_factor=replication
            )]
        )

        return True

    try:
        # CREATE THE GIVEN TOPIC
        create_topic(
            name=topic_name,
            partitions=num_partitions,
            replication=1
        )

    except Exception as err:
        log_func(err)

    # PRINT CURRENT KAFKA TOPIC STATE
    time.sleep(1)
    log_func(json.dumps(query_topics(), indent=4))

def test_topic(kafka_servers, topic_name, log_func=print):
    """ Test that the given topic is can send and receive messages """
    thread_lock = create_lock()
    time.sleep(2) # Allow topic to be created

    def cons(lock):
        kafka_client = create_consumer(topic_name, kafka_servers=kafka_servers)

        while lock.is_active():
            kafka_client.poll_next(1, lock, lambda *_: lock.kill())

    consumer_thread = Thread(target=cons, args=(thread_lock,))
    consumer_thread.start()
    time.sleep(2) # Allow thread to be launched

    max_attempts = 2
    # TODO: This does not seem to work well
    for i in range(max_attempts):
        log_func(f"Trying to send msg to {topic_name}")

        kafka_client = create_producer(kafka_servers=kafka_servers)
        kafka_client.push_msg(topic_name, json.dumps({"test": "testing"}).encode('UTF-8'))
        time.sleep(1)
        if not thread_lock.is_active():
            log_func(f"Received msg from topic {topic_name}")
            break  # Everything works
        else:
            log_func(f"Got nothing from topic {topic_name}")

    if thread_lock.is_active():
        log_func(f"Topic {topic_name} seems stuck...")
        thread_lock.kill()
    consumer_thread.join()


def clear_topic(kafka_servers, topic_name):
    """
    Clears all messages from the given topic by resetting the consumer group's offsets to the end.
    """
    try:
        # TODO: Clearing topics this way does not seem to work (produces errors)
        consumer_client = create_consumer(topic_name, kafka_servers=kafka_servers)

        # Get the partitions assigned to the consumer
        metadata = consumer_client.kafka_client.list_topics()
        partitions = [p for p in metadata.topics[topic_name].partitions.keys()]

        # Create TopicPartition objects for each partition
        topic_partitions = [TopicPartition(topic_name, p) for p in partitions]

        # Assign the consumer to the partitions
        consumer_client.kafka_client.assign(topic_partitions)

        # Seek to end for each partition
        for tp in topic_partitions:
            consumer_client.kafka_client.seek(tp)  # Default moves to the latest offset

        print(f"Cleared all messages in topic: {topic_name}")

    except Exception as e:
        print(f"Error clearing topic {topic_name}: {e}")

