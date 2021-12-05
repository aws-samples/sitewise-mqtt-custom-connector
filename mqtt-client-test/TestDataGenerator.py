#!/usr/bin/env python3
# /*
# __author__ = "Srikanth Kodali - skkodali@"
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# */

import json
import time
import logging.config
import random as rand
from random import *
import threading
import configparser
import pathlib
import traceback
from awscrt import io
from awsiot import mqtt_connection_builder
from awscrt import io
from awscrt.io import LogLevel
from awscrt.mqtt import Connection, Client, QoS
from awsiot.greengrass_discovery import DiscoveryClient, DiscoverResponse

'''
{
   "alias":"/EstrellaWinds/xandar/generator-model/86/Rpm",
   "messages":[
      {
         "name":"/EstrellaWinds/xandar/generator-model/86/Rpm",
         "value":206.0,
         "timestamp":1629161765999,
         "quality":"UNCERTAIN"
      }
   ]
}


{
    "propertyAlias" : string,
    "propertyId" : string,   # Optional
    "assetId" : string       # Optional
    "propertyValues" : [
        {
            "value": {
                "booleanValue" : boolean,    # Optional
                "doubleValue" : double,      # Optional
                "integerValue" : integer,    # Optional
                "stringValue" : string       # Optional
            },
            "timestamp": {
                "timeInSeconds": integer,
                "offsetInNanos": integer     # Optional
            },
            "quality": "string"
        }
    ]
}

{
    "propertyAlias" : "/EstrellaWinds/xandar/generator-model/86/Rpm",
    "propertyId" : string,   # Optional
    "assetId" : string       # Optional
    "propertyValues" : [
        {
            "value": {
                "doubleValue" : 206.0,      # Optional
            },
            "timestamp": {
                "timeInSeconds": 1629161765999
            },
            "quality": "GOOD"
        }
    ]
}

'''

logging.config.fileConfig(fname='config/log.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

file = pathlib.Path('config/conf.cfg')
config = configparser.ConfigParser()

if file.exists ():
    config.read(file)
else:
    logger.error("Config file: {} does not exists, please check if the file exists or not.".format(file))
    exit(1)

CERTS_PATH = config.get('mqtt-settings', 'CERTS_PATH')
certificate_path = config.get('mqtt-settings', 'certificate_file')
host_address = config.get('mqtt-settings', 'host')
port = config.getint('mqtt-settings', 'port')
root_ca_file = config.get('mqtt-settings', 'root_ca_file')
privatekey_file = config.get('mqtt-settings', 'privatekey_file')
thingName = config.get('mqtt-settings', 'thingName')
topic = config.get('mqtt-settings', 'topic')
region = config.get('mqtt-settings', 'region')

#CERTS_PATH = "~/iot-certs"
#certificate_path = "/home/ubuntu/iot-certs/asdasdqweqweqwesadasdasd9108-certificate.pem.crt"
#host_address = "172.31.43.144"
#port = 8883
#root_ca_file = "/home/ubuntu/iot-certs/AmazonRootCA1.pem"
#privatekey_file = "/home/ubuntu/iot-certs/asdasdqweqweqwesadasdasd9108-private.pem.key"
#thingName = "SiteWise_MQTT_Client_Thing"
#topic = "clients/dev1/sitewise/mqttiot"
#region = "us-east-1"

event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

tls_options = io.TlsContextOptions.create_client_with_mtls_from_path(CERTS_PATH + "/" + certificate_path, CERTS_PATH + "/" + privatekey_file)
if root_ca_file:
    tls_options.override_default_trust_store_from_path(None, CERTS_PATH + "/" + root_ca_file)
tls_context = io.ClientTlsContext(tls_options)

socket_options = io.SocketOptions()

logger.debug('Performing greengrass discovery...')
discovery_client = DiscoveryClient(client_bootstrap, socket_options, tls_context, region)
resp_future = discovery_client.discover(thingName)
discover_response = resp_future.result()

logger.debug(discover_response)

# This function is from basicDiscovery.py file.
# Try IoT endpoints until we find one that works
def try_iot_endpoints():
    for gg_group in discover_response.gg_groups:
        for gg_core in gg_group.cores:
            for connectivity_info in gg_core.connectivity:
                try:
                    logger.info('Trying core {} at host {} port {}'.format(gg_core.thing_arn, connectivity_info.host_address, connectivity_info.port))
                    mqtt_connection = mqtt_connection_builder.mtls_from_path(
                        endpoint=connectivity_info.host_address,
                        port=connectivity_info.port,
                        cert_filepath=CERTS_PATH + "/" + certificate_path,
                        pri_key_filepath= CERTS_PATH + "/" + privatekey_file,
                        client_bootstrap=client_bootstrap,
                        ca_bytes=gg_group.certificate_authorities[0].encode('utf-8'),
                        client_id=thingName,
                        clean_session=False,
                        keep_alive_secs=30)

                    connect_future = mqtt_connection.connect()
                    connect_future.result()
                    logger.info('Connected!')
                    return mqtt_connection

                except Exception as e:
                    logger.error('Connection failed with exception {}'.format(e))
                    continue

    logger.error('All connection attempts failed')

mqtt_connection = try_iot_endpoints()


class TestDataGenerator(object):
    @staticmethod
    def generate_measurement_for_an_asset(organization_name, location, asset_type, asset_unique_num, measurement_name, measurement_recorded_value, quality_value, recorded_time):
        equipment_tag_alias = "/" + str(organization_name) + "/" +  str(location) + "/" + str(asset_type) + "/" + str(asset_unique_num) + "/" + str(measurement_name)
        #print("tag is ::: {}".format(equipment_tag_alias))
        propertyValues = []
        measurement_value = {
            'doubleValue': measurement_recorded_value
        }
        measurement_timestamp = {
            'timeInSeconds': recorded_time
        }
        measurements = {
            'value': measurement_value,
            'timestamp': measurement_timestamp,
            'quality': quality_value
        }
        propertyValues.append(measurements)
        payload = {
            'propertyAlias': equipment_tag_alias,
            'propertyValues': propertyValues
        }
        logger.debug("Json payload message is :: {}".format(json.dumps(payload)))
        return json.dumps(payload)

    @staticmethod
    def wrapper_data_generator(sleep_interval):
        global config
        for k in range(5000):
            #for k in range(50):
            power = rand.randint(17, 27)
            temperature = rand.randint(20, 25)
            rpm = rand.randint(90, 130)
            quality = 'GOOD'
            seed = rand.randint(1,10)
            #logger.info("seed: {}".format(seed))
            if seed == 3 or seed == 6:
                power = rand.randint(0, 10)
                temperature = rand.randint(35, 45)
                rpm = rand.randint(50, 70)
                quality = 'BAD'
            elif seed == 7:
                power = rand.randint(10, 15)
                temperature = rand.randint(25, 35)
                rpm = rand.randint(190, 210)
                quality = 'UNCERTAIN'
            power = float(power)
            temperature = float(temperature)
            rpm = float(rpm)
            #timestamp_value = int(time.time() * 1000)
            timestamp_value = int(time.time())
            corp_name = config.get('organization', 'name')
            location_value = config.get('organization', 'plant-location')

            prop = config.items("equipments")
            equipment_type_values = list(dict(prop).values())
            equipment_type = rand.choice(tuple(equipment_type_values))
            logger.debug("Selected equipment type is: {}".format(equipment_type))

            model_asset_alias_mappings = dict(config.items(equipment_type+"-asset-alias-mappings"))
            measurements_list = list(model_asset_alias_mappings.values())

            # Todo: in future we need to generate these values based on the equipment type that we selected.
            # Todo: For gernerator, we might have 3 attributes and for hvac, we might have different values and attributes.
            # Todo: For simiplicity, we will assume both equipments has the same number of properties.
            measurement_values_list = [power, temperature, rpm]

            asset_uniq_num = randint(0, 99)
            for measurement, measurement_value in zip(measurements_list, measurement_values_list):
                result_payload = TestDataGenerator.generate_measurement_for_an_asset(corp_name, location_value, equipment_type, asset_uniq_num, measurement,  measurement_value, quality, timestamp_value)
                logger.debug("Resultant message is : {}".format(result_payload))
                pub_future, _ = mqtt_connection.publish(topic, result_payload, QoS.AT_MOST_ONCE)
                pub_future.result()
                logger.info('Published topic {}: {}\n'.format(topic, result_payload))
                #myAWSIoTMQTTClient.publish(topic, result_payload, 0)
                time.sleep(0.1)
            logger.debug("sleeping for 1 second")
            time.sleep(sleep_interval)
            k += 1

if __name__ == '__main__':
    #for i in range(4):
    for i in range(2):
        t = threading.Thread(target=TestDataGenerator.wrapper_data_generator, args=(1,))
        t.start()