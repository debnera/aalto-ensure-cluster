import json
import time
from threading import Thread

from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import TopicPartition


from .utils.kafka_utils import create_producer, create_consumer
from .utils.misc import create_lock


# PARSE PYTHON ARGUMENTS
def init_kafka(kafka_servers, topic_name, num_partitions=5):
    """
    Try to initialize kafka topics, so consumers and others do not complain about missing topics.

    Num_partitions should at minimum be equivalent to the total number of consumers in the cluster.
    """

    admin_client = AdminClient({
        'bootstrap.servers': kafka_servers,
    })

    # CHECK WHAT TOPICS EXIST
    def query_topics():
        container = {}

        for name, parts in admin_client.list_topics().topics.items():
            container[name] = len(parts.partitions)

        # print(json.dumps(container, indent=4))
        return container

    # CREATE TOPICS WITH N PARTITIONS OR ADJUST IF EXISTS
    def create_topic(name, partitions, replication):

        # CHECK CURRENT TOPICS
        topic_data = query_topics()

        # ADJUST PARTITIONS IF TOPIC ALREADY EXISTS
        if name in topic_data:
            current_partitions = topic_data[name]
            if current_partitions < partitions:
                admin_client.create_partitions(
                    {name: NewTopic.Partitions(partitions)}
                )
                print(f"INFO: TOPIC ({name}) PARTITIONS UPDATED FROM {current_partitions} TO {partitions}")
            else:
                print(f"INFO: TOPIC ({name}) ALREADY EXISTS WITH {current_partitions} PARTITIONS")
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
        print(err)

    # PRINT CURRENT KAFKA TOPIC STATE
    time.sleep(1)
    print(json.dumps(query_topics(), indent=4))

def test_topic(kafka_servers, topic_name):
    """ Test that the given topic is can send and receive messages """
    thread_lock = create_lock()

    def cons(lock):
        kafka_client = create_consumer(topic_name, kafka_servers=kafka_servers)

        while lock.is_active():
            kafka_client.poll_next(1, lock, lambda *_: lock.kill())

    consumer_thread = Thread(target=cons, args=(thread_lock,))
    consumer_thread.start()

    max_attempts = 1
    time.sleep(2)
    # TODO: This does not seem to work well, since the messages are consumed by the deployed pods
    for i in range(max_attempts):
        print(f"Trying to send msg to {topic_name}")

        kafka_client = create_producer(kafka_servers=kafka_servers)
        kafka_client.push_msg(topic_name, json.dumps({"test": "testing"}).encode('UTF-8'))
        time.sleep(2)
        if not thread_lock.is_active():
            print(f"Received msg from topic {topic_name}")
            break  # Everything works
        else:
            print(f"Got nothing from topic {topic_name}")

    if thread_lock.is_active():
        print(f"Topic {topic_name} seems stuck...")
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

