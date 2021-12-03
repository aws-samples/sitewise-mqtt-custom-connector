## Test data simulator program to push data into GGV1 MQTT broker from the publisher host
1)	Download a test data generator that will generate random values for the assets. It also sends the generated values to a topic `(clients/+/mqttiot/sitewise)` in the Greengrass’s MQTT broker that comes with Greengrass version 2.
```
$	cd ~
$	git clone <>
$	cd sitewise-mqtt/mqtt-client-test/
$	cd config/
```
Change the values in `conf.cfg` file with your certs files that we copied in the `~/iot-certs` folder.

| Num | Property | Change to | 
| --- | --- |  --- |
| 1	| CERTS_PATH | This the cert file’s location that you have created. If you follow the instructions in the blog the value will be `/home/ubuntu/iot-certs` | 
| 2	| host | This will be your Greengrass core device host IP address. In this case, you can get the IP address of the Greengrass core device by logging into the 1st EC2 instance that was created in Step 2. Run the command: `hostname -I` to get the IP address of your Greengrass core device. | 
| 3	| root_ca_file | This will be your root ca file. In our case it is `AmazonRootCA1.pem`. Make sure you have named the root ca file with this name, otherwise change this value as needed. | 
| 5	| certificate_file | This will be your thing’s/device’s certificate file. Replace the `<hash>` with your cert’s hash value. This is also in your `~/iot-certs` folder. The value will be: `<hash>-certificate.pem.crt` | 
| 6	| privatekey_file |	This will be your thing’s/device’s private key file. Replace the `<hash>` with your cert’s hash value. This is also in your `~/iot-certs` folder. The value will be: `<hash>-private.pem.key` | 
| 7	| thingName | This will be your publisher device’s thing name. In this case, our thing name is: `Sitewise_MQTT_Client_Thing`. | 
| 8	| topic	| This will be the topic name that you have set during the Enable Client device support in Step #3. In our case it was set to `“clients/+/mqttiot/sitewise”`. So you can replace `“+”` with `“any value”`. In this case, we will use: `“clients/dev1/mqttiot/sitewise”`. | 
| 9	| Region | By default, this blog assumes all the previous assets were created in us-east-1 region. So the value will be `“us-east-1”`. | 

2)	Execute the Test data generator program so that it will generate some data set and will send to Greengrass MQTT broker.
After updating the configuration values in the previous step, run the below commands.

Make sure, the publisher/client device and Greengrass core device are in the same network. The publisher/client device needs to connect to Greengrass core device on port number 8883. If your client and Greengrass core devices are EC2 instances, then allow port 8883 in security groups. 

```
$ cd ~/sitewise-mqtt/mqtt-client-test
$ chmod -R 755 TestDataGenerator.py
$ python3 TestDataGenerator.py
```

This will start publishing the messages. When you want to stop generating the data, just press `“ctrl+c”` to exit out of the program.

Now you can go to AWS IoT Sitewise console and see the data is getting populated. Go to Assets, then select one of the assets where the data got populated from the above test data generator. And go to `“Measurements”` and you should see values under Latest value column.
