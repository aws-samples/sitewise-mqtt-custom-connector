## AWS IoT Sitewise MQTT connector with AWS IoT Greengrass version 2
### sitewise-assets-creation
```
This module has the scripts that creates AWS IOT SiteWise assets and models.
```
### mqtt-client-test.
```
This module has the scripts that generates random test data that publish the data to assets that are created with the sitewise-assets-creation module. 
```
### mqtt-to-sitewise-connector-component.
```
This module has the custom Greengrass component that will read the messages from the Greengrass V2 MQTT broker and will send to AWS IoT SiteWise/AWS IoT SiteWise Edge through AWS IoT Greengrass Stream manager.  
```
