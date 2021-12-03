## Create sample AWS IoT Sitewise asset models and assets in your AWS account

In this step, we will setup the AWS IoT Sitewise asset models and assets. To do so, we will use an AWS CDK script that will generate asset models and assets in your AWS IoT Sitewise console.

You can use this downloadable scripts to setup the assets and asset models. Once you download this repo onto your local computer/mac, run the below commands.

Note: Make sure you installed `aws_cdk` in your python environment before running the below commands. Otherwise, you will get `“No module named ‘aws_cdk’`.

```
git clone <>
cd <Downloaded location>
cd sitewise-assets-creation/
cdk bootstrap aws://<YOUR_AWS_ACCOUNT_NUMBER>/<AWS_REGION> --profile <AWS_CLI_PROFILE_NAME>
cdk deploy sitewise-assets-creation --profile <AWS_CLI_PROFILE_NAME>
```

Once the above CDK script execution is completed, it will create two AWS IoT Sitewise asset models named as: `1) generator-model` and `2) hvac-model.`
You can check these models by logging into the AWS IoT Sitewise console in your AWS account.
