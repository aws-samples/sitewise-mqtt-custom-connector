#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from awscrt import io
from awsiot import mqtt_connection_builder
from awsiot.greengrass_discovery import DiscoveryClient, DiscoverResponse

CERTS_PATH = "~/iot-certs"
certificate_path = "/home/ubuntu/iot-certs/96d7b827fccbb9ee191818076d394609163bf77125e60ffe55bb109f29ed9108-certificate.pem.crt"
host_address = "172.31.43.144"
port = 8883
root_ca_file = "/home/ubuntu/iot-certs/AmazonRootCA1.pem"
privatekey_file = "/home/ubuntu/iot-certs/96d7b827fccbb9ee191818076d394609163bf77125e60ffe55bb109f29ed9108-private.pem.key"
thingName = "SiteWise_MQTT_Client_Thing"
topic = "clients/dev1/sitewise/mqttiot"
region = "us-east-1"

event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

tls_options = io.TlsContextOptions.create_client_with_mtls_from_path(certificate_path, privatekey_file)
if root_ca_file:
    tls_options.override_default_trust_store_from_path(None, root_ca_file)
tls_context = io.ClientTlsContext(tls_options)

socket_options = io.SocketOptions()

print('Performing greengrass discovery...')
discovery_client = DiscoveryClient(client_bootstrap, socket_options, tls_context, region)
resp_future = discovery_client.discover(thingName)
discover_response = resp_future.result()

print(discover_response)

# Try IoT endpoints until we find one that works
def try_iot_endpoints():
    for gg_group in discover_response.gg_groups:
        for gg_core in gg_group.cores:
            for connectivity_info in gg_core.connectivity:
                try:
                    print('Trying core {} at host {} port {}'.format(gg_core.thing_arn, connectivity_info.host_address, connectivity_info.port))
                    mqtt_connection = mqtt_connection_builder.mtls_from_path(
                        endpoint=connectivity_info.host_address,
                        port=connectivity_info.port,
                        cert_filepath="/home/ubuntu/iot-certs/96d7b827fccbb9ee191818076d394609163bf77125e60ffe55bb109f29ed9108-certificate.pem.crt",
                        pri_key_filepath="/home/ubuntu/iot-certs/96d7b827fccbb9ee191818076d394609163bf77125e60ffe55bb109f29ed9108-private.pem.key",
                        client_bootstrap=client_bootstrap,
                        ca_bytes=gg_group.certificate_authorities[0].encode('utf-8'),
                        client_id=thingName,
                        clean_session=False,
                        keep_alive_secs=30)

                    connect_future = mqtt_connection.connect()
                    connect_future.result()
                    print('Connected!')
                    return mqtt_connection

                except Exception as e:
                    print('Connection failed with exception {}'.format(e))
                    continue

    exit('All connection attempts failed')

mqtt_connection = try_iot_endpoints()

if __name__ == '__main__':
    print("hello")