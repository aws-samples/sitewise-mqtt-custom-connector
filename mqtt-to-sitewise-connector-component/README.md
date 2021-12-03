## Create an AWS IoT Greengrass component that collects the data stream from Greengrass core’s MQTT broker and sends to AWS IoT Sitewise

Download the git repo code on to your local mac or windows machine. Make sure you have AWS CLI is setup and configured with your AWS account credentials 
so that you can run the `“aws”` commands from the terminal/command prompt.

Run the below steps on your mac/pc. The `ddeploy-mqtt-connector.sh` script will create an artifacts compressed file, 
creates an s3 bucket in your AWS account to store the artifacts, prepares the deployment configuration file and the recipe files. 
Finally, it will deploy the component to your Greengrass core device.

This script takes two arguments.
```
1.	First argument is your IOT Thing group. This will be the name of the IoT Thing Group that your Greengrass core device belongs to.
2.	Second argument is your AWS Account number.
```
```
> cd ~
> git clone <>
> cd sitewise-mqtt-ggv2/mqtt-to-sitewise-connector-component/
```

Export AWS credentials, Make sure you have appropriate permissions.

```
> export AWS_ACCESS_KEY_ID="XXXXXXXXXXXXXXXXXXX"
> export AWS_SECRET_ACCESS_KEY="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

Run `“ddeploy-mqtt-connector.sh”` script.

```
> bash ./ ddeploy-mqtt-connector.sh <IOT_THING_GROUP> <AWS_ACCOUNT_NUMBER>
```

Once the deployment is successful, you can login to the Greengrass core device and can check the component log files.

```
> sudo su – 
> cd /greengrass/v2/logs
> tail -f community.greengrass.MqttToSitewise.log
```

You will see the below messages in the log file.
```
2021-08-25T20:28:50.793Z [INFO] (Copier) community.greengrass.MqttToSitewise: stdout. 2021-08-25 20:28:50,793 - dev - INFO - Total processed messages were : 0. {scriptName=services.community.greengrass.MqttToSitewise.lifecycle.Run, serviceName=community.greengrass.MqttToSitewise, currentState=RUNNING}
```

