# __author__ = "Srikanth Kodali - skkodali@"
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# */

import awsiot.greengrasscoreipc.client as client
from _SendToStreamManager import init_gg_stream_manager
from _SendToStreamManager import append_to_gg_stream_manager
from awsiot.greengrasscoreipc.model import (
    SubscribeToTopicRequest,
    SubscriptionResponseMessage
)
from awscrt.io import (
    ClientBootstrap,
    DefaultHostResolver,
    EventLoopGroup,
    SocketDomain,
    SocketOptions,
)
from awsiot.eventstreamrpc import Connection, LifecycleHandler, MessageAmendment
from os import path
import sys
import threading, queue
import os
import time
import logging.config
import configparser
import pathlib
import traceback
import json
from threading import Thread
import queue
import os

log_file_path = path.join(path.dirname(path.abspath(__file__)), 'config/log.conf')
logging.config.fileConfig(log_file_path)

#logging.config.fileConfig(fname='config/log.conf', disable_existing_loggers=False)
logger = logging.getLogger('dev')

config_file_path = path.join(path.dirname(path.abspath(__file__)), 'config/mqtt-connector.conf')
file = pathlib.Path(config_file_path)
config = configparser.ConfigParser()

if file.exists ():
    config.read(file)
else:
    logger.error("Config file: {} does not exists, please check if the file exists or not.".format(file))
    exit(1)

TIMEOUT = 10
#TOPIC="clients/dev1/sitewise/mqttiot"
tags_dict = {}
q = queue.Queue()
region = os.environ.get('AWS_REGION')

wait_time = config.getint('mqtt-settings', 'wait_time')
stream_name = config.get('mqtt-settings', 'stream_name')
TOPIC = config.get('mqtt-settings', 'topic')


try:
    logger.info("Initiating Stream manager client with stream name : {}.".format(stream_name))
    sitewise_stream_client = init_gg_stream_manager(stream_name)
    logger.info("Completed stream manager initiation")
except (ValueError, Exception):
    logger.error("Exception occurred while creating the sitewise stream client : %s", traceback.format_exc())

def send_to_stream_manager():
    global tags_dict
    logger.info("Flushing batch of messages to greengrass stream manager.")
    for key, value in list(tags_dict.items()):
        logger.debug("The metrics for the current alias/tag: {} are: {}".format(key, value))
        payload_to_streammanager = {"propertyAlias": key, "propertyValues": value}
        logger.info("Payload that is going to stream manager is: {}".format(payload_to_streammanager))
        try:
            logger.debug("Appending to stream manager.")
            append_to_gg_stream_manager(sitewise_stream_client, stream_name, json.dumps(payload_to_streammanager).encode())
        except (ValueError, Exception):
            logger.error("Exception occurred while appending the message to stream manager: %s", traceback.format_exc())
        logger.debug("Payload sent to stream manager successfully.")
        try:
            tags_dict.pop(key)
        except KeyError:
            logger.error("Exception occurred while flushing the dictionary: %s", traceback.format_exc())

class IPCUtils:
    def __init__(self):
        self.lifecycle_handler = LifecycleHandler()

    def connect(self):
        elg = EventLoopGroup()
        resolver = DefaultHostResolver(elg)
        bootstrap = ClientBootstrap(elg, resolver)
        socket_options = SocketOptions()
        socket_options.domain = SocketDomain.Local
        amender = MessageAmendment.create_static_authtoken_amender(os.getenv("SVCUID"))
        hostname = os.getenv("AWS_GG_NUCLEUS_DOMAIN_SOCKET_FILEPATH_FOR_COMPONENT")
        connection = Connection(
            host_name=hostname,
            port=8033,
            bootstrap=bootstrap,
            socket_options=socket_options,
            connect_message_amender=amender,
        )
        connect_future = connection.connect(self.lifecycle_handler)
        connect_future.result(TIMEOUT)
        return connection

class StreamHandler(client.SubscribeToTopicStreamHandler):
    def __init__(self):
        super().__init__()
    def on_stream_event(self, event: SubscriptionResponseMessage) -> None:
        # message_string = str(event.binary_message.message, "utf-8")
        logger.info("Step message from IPC recevied at : {}".format(time.time()))
        try:
            receiver_payload: str = event.binary_message.message.decode("utf-8")
            logger.info("Received message from the GG IPC topic is {}.".format(receiver_payload))
            q.put(receiver_payload)
            logger.debug("Message sent to queue at : {}".format(time.time()))
            #logger.info("Message sent to queue - put completed. - Queue size is {}".format(q.qsize()))
        except (ValueError, Exception):
            logger.error("Exception - Failed during reading message from event - ", traceback.format_exc())

    def on_stream_error(self, error: Exception) -> bool:
        # Handle error.
        return True

    def on_stream_closed(self) -> None:
        pass

class MySubscriber:
    i = 0
    stream_s3_client = None

    # noinspection PyMethodMayBeStatic
    def subscribe(self, sub_ipc_client):
        request = SubscribeToTopicRequest()
        request.topic = TOPIC
        handler = StreamHandler()
        operation = sub_ipc_client.new_subscribe_to_topic(handler)
        future = operation.activate(request)
        future.result(TIMEOUT)
        #print("SRIKANTH SUBSCRIBER DEBUG : Completed all the steps...", flush=True)
        #operation.close()

    @staticmethod
    def init_ipc_connection():
        ipc_utils = IPCUtils()
        connection = ipc_utils.connect()
        ipc_client = client.GreengrassCoreIPCClient(connection)
        return ipc_client

    # noinspection PyMethodMayBeStatic
    def handle_message(self, handle_ipc_payload_from_queue: str):
        start_time = time.time()
        logger.info("In handle messages - Message is : {}".format(handle_ipc_payload_from_queue))


def handle_metric_message(handle_metric_payload):
    global tags_dict
    logger.debug("Message payload is ::: {}".format(handle_metric_payload))
    handle_metric_payload = json.loads(handle_metric_payload)
    tag_alias = handle_metric_payload["propertyAlias"]
    msg_payload = handle_metric_payload["propertyValues"][0]
    logger.debug("Message payload is ::: {}".format(msg_payload))
    logger.info("Message payload is ::: {}".format(msg_payload))
    if tags_dict.get(tag_alias) :
        tags_dict[tag_alias].append(msg_payload)
        logger.info("The current size for tag/alias: {} is: {}".format(tag_alias, len(tags_dict[tag_alias])))
    else:
        logger.info("Initialzing the dictionary for tag/alias: {}: ".format(tag_alias))
        tags_dict[tag_alias] = [msg_payload]

def process_queue_and_send_to_stream_manager():
    logger.debug("In Process queue and send to stream manager function")
    while True:
        count = 0
        total_loop_messages = q.qsize()
        logger.debug("Total number of messages in the queue are : {}".format(total_loop_messages))
        for element in range(total_loop_messages):
            try:
                payload = q.get()
            except queue.Empty:
                logger.error("Exception occurred while getting the elements from the queue: %s", traceback.format_exc())
            logger.debug("Message number is : {}/{} and Message pay load after getting it from the queue is : {}".format(count, total_loop_messages, payload))
            handle_metric_message(payload)
            count += 1
        logger.info("Total processed messages were : {}".format(count))
        if count > 0:
            send_to_stream_manager()
        #wait_time = config.getint('mqtt-settings', 'wait_time')
        logger.info("Pausing for {} seconds to collect new messages.".format(str(wait_time)))
        time.sleep(wait_time)
        logger.info("Pause completed. Going to next iteration.")

t1 = Thread(target=process_queue_and_send_to_stream_manager)
t1.start()

if __name__ == "__main__":
    sub = MySubscriber()
    logger.debug("Initiating ipc connection")
    m_ipc_client = sub.init_ipc_connection()
    logger.debug("IPC connection was initiated successfully")
    #sub.init_stream_manager_client()
    logger.debug("Calling subscribe method")
    sub.subscribe(m_ipc_client)

    '''while True:
        count = 0
        for element in range(q.qsize()):
            logger.debug("Total number of messages in the queue are : {}".format(q.qsize()))
            try:
                payload = q.get()
            except queue.Empty:
                logger.error("Exception occurred while getting the elements from the queue: %s", traceback.format_exc())
            logger.debug("In While loop - Message pay load after getting it from the queue is : {}".format(payload))
            handle_metric_message(payload)
            count += 1
        logger.info("Total processed messages were : {}".format(count))
        if count > 0:
            logger.info("Sending to stream manager.")
            send_to_stream_manager()
        #wait_time = config.getint('mqtt-settings', 'wait_time')
        logger.info("Pausing for {} seconds to collect new messages.".format(str(wait_time)))
        time.sleep(wait_time)
        logger.info("Pause completed. Going to next iteration.")
    '''



