import json

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError


def connector_name_from_key(key):
    # what we get: key = b'["test-source", {"filename": "/tmp/test.txt"}]'
    key_obj = json.loads(key)
    for item in key_obj:
        # we return the first item that is a string (JSON loads doesn't guarantee the ordering of the parsed object)
        if isinstance(item, str):
            return item
    return None


def create_tombstone_msg(kafka_url, connector_name, offset_storage_topic):
    # it'd be nice to get the offset_storage_topic name programmatically
    # but it doesn't seem to be possible using the Connect REST API

    # read the last message for the connector
    consumer = KafkaConsumer(offset_storage_topic,
                             bootstrap_servers=kafka_url,
                             auto_offset_reset='earliest',
                             enable_auto_commit=False,
                             consumer_timeout_ms=2500,
                             )

    messages_written = []
    latest_messages = {} # map of message key --> partition number

    for message in consumer:
        if connector_name_from_key(message.key) == connector_name:
            latest_messages[message.key] = message.partition

    # write a null tombstone msg to the proper broker for each unique key used by the connector
    producer = KafkaProducer(bootstrap_servers=kafka_url)
    TIMEOUT = 10

    for message_key, partition in latest_messages.items():
        messages_written.append(message_key)
        # print(f"writing tombstone msg for {message_key}")
        future = producer.send(offset_storage_topic, key=message_key, value=None, partition=partition)
        try:
            future.get(timeout=TIMEOUT)
        except KafkaError:
            raise RuntimeError(f"Failed to write tombstone message within the imparted time ({TIMEOUT}s)")

    return messages_written
