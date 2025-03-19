from confluent_kafka import Consumer, Producer
from utilz.misc import log
import sys

# GOOD DOCS FOR CONSUMER API
    # https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#consumer
    # https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#producer

###################################################################################################
###################################################################################################

KAFKA_SERVERS = '130.233.193.117:10001'
# KAFKA_SERVERS = 'localhost:10001,localhost:10002,localhost:10003'
VERBOSE = True

###################################################################################################
###################################################################################################

class create_producer:

    # ON LOAD, CREATE KAFKA PRODUCER
    def __init__(self):
        self.kafka_client = Producer({
            'bootstrap.servers': KAFKA_SERVERS,
        })

    # MAKE SURE KAFKA CONNECTION IS OK
    def connected(self):
        try:
            metadata = self.kafka_client.list_topics(timeout=2)
            log('SUCCESSFULLY CONNECTED TO KAFKA')
            return True
        except:
            log(f'COULD NOT CONNECT WITH KAFKA SERVER ({KAFKA_SERVERS})')
            return False

    # ON CONSUMER CALLBACK, DO..
    def ack_callback(self, error, message):
        if error:
            print('ACK ERROR', error)
        else:
            if VERBOSE: log(f'MESSAGE PUSHED')

    # PUSH MESSAGE TO A KAFK TOPIC
    def push_msg(self, topic_name, bytes_data):

        # PUSH MESSAGE TO KAFKA TOPIC
        self.kafka_client.produce(
            topic_name, 
            value=bytes_data,
            on_delivery=self.ack_callback,
        )

        # ASYNCRONOUSLY AWAIT CONSUMER ACK BEFORE SENDING NEXT MSG
        self.kafka_client.poll(1)
        # self.kafka_client.flush()

###################################################################################################
###################################################################################################

class create_consumer:

    # ON LOAD, CREATE KAFKA CONSUMER CLIENT
    def __init__(self, kafka_topic):

        # SET STATIC CONSUMPTION CONFIGS
        self.kafka_topic = kafka_topic

        # CREATE THE CONSUMER CLIENT
        self.kafka_client = Consumer({
            'bootstrap.servers': KAFKA_SERVERS,
            'group.id': kafka_topic + '.consumers',
            'enable.auto.commit': False,
            'on_commit': self.ack_callback,
            'auto.offset.reset': 'latest',
            # 'auto.offset.reset': 'earliest'
        })

        # SUBSCRIBE TO THE KAFKA TOPIC
        self.kafka_client.subscribe([kafka_topic], self.assigned, self.revoked, self.lost)

    # WHEN CLASS DIES, KILL THE KAFKA CLIENT
    def __del__(self):
        log('KAFKA CLIENT CLOSED')
        self.kafka_client.close()

    # PARTITION ASSIGNMENT SUCCESS
    def assigned(self, consumer, partition_data):
        if VERBOSE:
            partitions = [p.partition for p in partition_data]
            log(f'CONSUMER ASSIGNED PARTITIONS: {partitions}')

    # PARTITION ASSIGNMENT REVOKED
    def revoked(self, consumer, partition_data):
        if VERBOSE:
            partitions = [p.partition for p in partition_data]
            log(f'CONSUMER PARTITION ASSIGNMENT REVOKED: {partitions}')

    # PARTITION ASSIGNMENT LOST
    def lost(self, consumer, partition_data):
        log(f'CONSUMER ASSIGNMENT LOST: {consumer} {partition_data}')

    # MAKE SURE KAFKA CONNECTION IS OK
    def connected(self):
        try:
            metadata = self.kafka_client.list_topics(timeout=2)
            log('SUCCESSFULLY CONNECTED TO KAFKA')
            return True
        except:
            log(f'COULD NOT CONNECT WITH KAFKA SERVER ({KAFKA_SERVERS})') 
            return False

    # AUTO CALLBACK WHEN CONSUMER COMMITS MESSAGE
    def ack_callback(self, error, partitions):
        if error:
            return print('ACK ERROR', error)

    # START CONSUMING TOPIC EVENTS
    def poll_next(self, nth_thread, thread_lock, on_message):
        log(f'THREAD {nth_thread}: NOW POLLING')
        
        # KEEP POLLING WHILE LOCK IS ACTIVE
        while thread_lock.is_active():
            try:
                # POLL NEXT MESSAGE
                msg = self.kafka_client.poll(1)

                # NULL MESSAGE -- SKIP
                if msg is None:
                    continue

                # CATCH ERRORS
                if msg.error():
                    print('FAULTY EVENT RECEIVED', msg.error())
                    continue

                # COMMIT THE EVENT TO PREVENT OTHERS FROM TAKING IT
                self.kafka_client.commit(msg, asynchronous=True)

                # HANDLE THE EVENT VIA CALLBACK FUNC
                if VERBOSE: log(f'THREAD {nth_thread}: EVENT RECEIVED ({self.kafka_topic})')
                on_message(msg.value(), nth_thread)
                if VERBOSE: log(f'THREAD {nth_thread}: EVENT HANDLED')

            # SILENTLY DEAL WITH OTHER ERRORS
            except Exception as error:
                print('CONSUMER ERROR', error)
                continue
            
        # LOCK WAS KILLED, THEREFORE THREAD LOOP ENDS
        log(f'THREAD {nth_thread}: MANUALLY KILLED')
