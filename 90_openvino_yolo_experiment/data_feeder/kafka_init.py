from confluent_kafka.admin import AdminClient, NewPartitions, NewTopic
from confluent_kafka import TopicPartition
import json, time, argparse

from .utilz.kafka_utils import create_producer, create_consumer
from .utilz.misc import create_lock
from threading import Thread

# PARSE PYTHON ARGUMENTS
def init_kafka(kafka_servers, num_partitions=5):
    """
    Try to initialize kafka topics, so yolo_consumer and others do not complain about missing topics.

    Num_partitions should at minimum be equivalent to the total number of yolo_consumers in the cluster.
    """

    admin_client = AdminClient({
        'bootstrap.servers': kafka_servers,
    })

    # CHECK WHAT TOPICS EXIST
    def query_topics():
        container = {}

        for name, parts in admin_client.list_topics().topics.items():
            container[name] = len(parts.partitions)

        #print(json.dumps(container, indent=4))
        return container

    # CREATE TOPICS WITH N PARTITIONS
    def create_topic(name, partitions, replication):

        # CHECK CURRENT TOPICS
        topic_data = query_topics()

        # STOP IF TOPIC ALREADY EXISTS
        if name in topic_data:
            raise Exception(f'ERROR: TOPIC ({name}) ALREADY EXISTS')

        # OTHERWISE, CREATE IT
        admin_client.create_topics(
            new_topics=[NewTopic(
                topic=name,
                num_partitions=partitions,
                replication_factor=replication
            )]
        )

        return True

    ###########################################################################################
    ###########################################################################################

    try:
        # CREATE YOLO INPUT TOPIC WITH 34 PARTITIONS
        create_topic(
            name='yolo_input',
            partitions=num_partitions,
            replication=1
        )

        # CREATE VALIDATION TOPIC
        create_topic(
            name='yolo_output',
            partitions=1,
            replication=1
        )

    except Exception as err:
        print(err)

    # PRINT CURRENT KAFKA TOPIC STATE
    time.sleep(1)
    print(json.dumps(query_topics(), indent=4))

    ###################################################################################
    ###################################################################################

    def test_topic(topic_name):
        thread_lock = create_lock()

        def cons(lock):
            kafka_client = create_consumer(topic_name, kafka_servers=kafka_servers)

            while lock.is_active():
                kafka_client.poll_next(1, lock, lambda *_: lock.kill())

        consumer_thread = Thread(target=cons, args=(thread_lock,))
        consumer_thread.start()

        max_attempts = 10
        time.sleep(2)
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

    test_topic('yolo_input')
    test_topic('yolo_output')
