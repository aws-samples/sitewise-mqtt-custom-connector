#!/bin/bash
# /*
# __author__ = "Srikanth Kodali - skkodali@"
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# */

_setEnv()
{
  AWS="aws"
  #echo "DEV_IOT_THING_GROUP: ${DEV_IOT_THING_GROUP}"
  echo "DEV_IOT_THING: ${DEV_IOT_THING}"
  echo "AWS_ACCOUNT_NUMBER: ${AWS_ACCOUNT_NUMBER}"
  AWS_REGION="us-east-1"
  CURRENT_VERSION_NUMBER="1.0.0"
  COMPONENT_NAME="community.greengrass.MqttToSitewise"
  export LC_CTYPE=C #If you run on mac < bigsur
  export LC_ALL=C # If you run on mac bigsur
  RANDOM_SUFFIX=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1`
  echo ${RANDOM_SUFFIX}
  S3_BUCKET="ggv2-mqtt-to-sitewise-component-${RANDOM_SUFFIX}"
  S3_KEY="artifacts"
  S3_PATH="s3://${S3_BUCKET}/${S3_KEY}/${COMPONENT_NAME}"
  SRC_FOLDER="src"
  ARTIFACTS_ARCHIVE_FILE_NAME="mqtt-to-sitewise-artifacts"
  MAIN_ARTIFACT_FILE="MqttToSiteWiseGGV2.py"
  DEPLOYMENT_CONFIG_TEMPLATE_FILE="deployment_configuration_template.json"
  DEPLOYMENT_CONFIG_FILE="deployment_configuration.json"
}

_installSigil()
{
    if ! [ -x "$(command -v sigil)" ]; then
      echo 'Error: git is not installed.' >&2
      curl -kL "https://github.com/gliderlabs/sigil/releases/download/v0.6.0/sigil_0.6.0_$(uname -sm|tr \  _).tgz" | sudo tar -zxC /usr/local/bin
      which sigil
    else
      echo "Sigil is already installed."
    fi
}

_check_if_jq_exists() {
  JQ=`which jq`
  if [ $? -eq 0 ]; then
    echo "JQ exists."
  else
    echo "jq does not exists, please install it."
    echo "EXITING the program."
    exit 1;
  fi
}

_checkIfABucketWithPrefixExists()
{
  bucket_list=""
  bucket_list=`aws s3 ls | awk '{print $3}'`
  if [[ ${bucket_list[@]} ]]; then
      echo ${bucket_list[@]}
      #if printf '%s\n' "${bucket_list[@]}" | grep -q -P 'ggv2-mqtt-to-sitewise-component-'; then
      if printf '%s\n' "${bucket_list[@]}" | grep 'ggv2-mqtt-to-sitewise-component-'; then
        echo "Bucket with prefix exists."
        #S3_BUCKET=`printf '%s\n' "${bucket_list[@]}" | grep -P 'ggv2-mqtt-to-sitewise-component-'`
        S3_BUCKET=`printf '%s\n' "${bucket_list[@]}" | grep 'ggv2-mqtt-to-sitewise-component-'`
        echo $S3_BUCKET
        S3_KEY="artifacts"
        S3_PATH="s3://${S3_BUCKET}/${S3_KEY}/${COMPONENT_NAME}"
        echo "S3_PATH IS: ${S3_PATH}"
      else
        echo "Bucket is being created."
        aws s3api create-bucket --bucket ${S3_BUCKET} --region ${AWS_REGION}
      fi
  else
      echo "Error accessing S3 buckets, please check the error. Exiting."
      exit 1;
  fi
}

_getNextVersion() 
{
  DELIMETER="."
  target_index=${2}
  #full_version=($(echo "$1" | tr '.' '\n'))
  full_version=""
  IFS='.' read -r -a full_version <<< "$1"
  #declare -a full_version=($(echo "$1" | tr "$DELIMETER" " "))
  for index in ${!full_version[@]}; do
    if [ $index -eq $2 ]; then
      local value=full_version[$index]
      value=$((value+1))
      full_version[$index]=$value
      break
    fi
  done
  NEXT_VERSION=`echo $(IFS=${DELIMETER} ; echo "${full_version[*]}")`
}

_compressArtifactsAndPushToCloud()
{
  SRC_FOLDER_ARG=$1
  PRJ_ARG=$2
  PWDIR=`pwd`
  echo $PWDIR
  cd ${SRC_FOLDER_ARG}
  echo $PRJ_ARG
  zip -r ${PRJ_ARG}.zip .
  ls -ltra
  ${AWS} s3 cp ${PRJ_ARG}.zip ${S3_PATH}/${NEXT_VERSION}/
  cd ${PWDIR}
  ls -ltra
}

_create_gg_component_in_cloud()
{
  REC_FILE_ARG=$1
  RECIPE_URI="fileb://${REC_FILE_ARG}"
  echo "Creating components in the cloud."
  #RES=`${AWS} greengrassv2 create-component-version --inline-recipe ${RECIPE_URI} --region ${AWS_REGION}`
  ARN=$(${AWS} greengrassv2 create-component-version --inline-recipe ${RECIPE_URI} --region ${AWS_REGION} | jq -r ".arn")
  echo "ARN is : "
  echo ${ARN}
  AWS_ACCOUNT_NUM=`echo ${ARN} | cut -d ":" -f 5`
  #${AWS} greengrassv2 describe-component --arn "" --region ${AWS_REGION}
}

_prepare_deployment_config_file()
{
  sigil -p -f ${DEPLOYMENT_CONFIG_TEMPLATE_FILE} \
    component_name=$COMPONENT_NAME \
    component_version_number=${NEXT_VERSION} > ${DEPLOYMENT_CONFIG_FILE}
}

_get_index_value_from_array()
{
  comp_ver_array="$1"
  echo "${!comp_ver_array[@]}"
  for i in "${!comp_ver_array[@]}";
  do
     echo "In for loop : ${i}"
     echo "${comp_ver_array[$i]}"
     echo "${COMPONENT_NAME}"
     if [[ "${comp_ver_array[$i]}" = "${COMPONENT_NAME}" ]]; then
         echo "MATCH FOUND AT : ${i}";
         index_val=${i}        
         break;
     fi
  done 
}

_get_index_value_from_array_with_comp_name()
{
  local c_name="$1"
  shift
  local c_ver_array=("$@")
  #echo "In the function : count is : ${!c_ver_array[@]}"
  #echo "In the function : ${c_ver_array[@]}"
  for i in "${!c_ver_array[@]}";
  do
     if [[ "${c_ver_array[$i]}" = "${c_name}" ]]; then
         echo "MATCH FOUND AT : ${i}";
         c_index_val=${i}        
         break;
     fi
  done 
}

_prepare_deployment_config_file_based_on_deployment_name()
{
  DEPLOY_FILE_ARG=$1
  COMP_NAME=$2
  COMP_VERSION=""
  
  #THING_GROUP_ARN="arn:aws:iot:${AWS_REGION}:${AWS_ACCOUNT_NUMBER}:thinggroup/${DEV_IOT_THING_GROUP}"
  #THING_GROUP_ARN="arn:aws:iot:${AWS_REGION}:${AWS_ACCOUNT_NUMBER}:thinggroup/${DEV_IOT_THING}"
  THING_ARN="arn:aws:iot:${AWS_REGION}:${AWS_ACCOUNT_NUMBER}:thing/${DEV_IOT_THING}"
  deployment_id=`aws greengrassv2 list-deployments --target-arn ${THING_ARN} | jq -r '.deployments[]' | jq -r .deploymentId`
  echo "Deployment Id is : ${deployment_id}"

  ### Check if the component was created previously and used in other thing groups.

  EXITING_COMP_VERSION=`aws greengrassv2 list-components | jq -r '.components[] | select(.componentName == "'"${COMP_NAME}"'").latestVersion' | jq -r '.componentVersion'`
  echo "Existing comp version is : ${EXITING_COMP_VERSION}"

  if [[ ! ${EXITING_COMP_VERSION} = "null" ]]; then
      _getNextVersion ${EXITING_COMP_VERSION} 2
      CURRENT_VERSION_NUMBER=${NEXT_VERSION}
      echo "When existing component found in this account, then CURRENT_VERSION_NUMBER is : ${CURRENT_VERSION_NUMBER}"
  fi

  if [[ -z "${deployment_id}" ]]; then
    #echo "There is no deployment for this thinggroup : ${DEV_IOT_THING_GROUP} yet."
    echo "There is no deployment for this thing : ${DEV_IOT_THING} yet."
    STR1='{"'
    STR2=${COMP_NAME}
    STR3='": {"componentVersion": '
    STR4=${CURRENT_VERSION_NUMBER}
    STR5='}}'
    NEW_CONFIG_JSON=$STR1$STR2$STR3\"$STR4\"$STR5
    echo ${NEW_CONFIG_JSON}
    NEXT_VERSION=${CURRENT_VERSION_NUMBER}
  else
    COMP_VERSION=`aws greengrassv2 get-deployment --deployment-id ${deployment_id} | jq .'components' | jq '."'"${COMP_NAME}"'"' | jq -r ."componentVersion"`
    if [[ ! ${COMP_VERSION} = "null" ]]; then
      _getNextVersion ${COMP_VERSION} 2
    fi
    #echo $NEXT_VERSION
    NEW_CONFIG_JSON=`aws greengrassv2 get-deployment --deployment-id ${deployment_id} | jq .'components' | jq 'del(."$COMP_NAME")' | jq  '. += {"'"$COMP_NAME"'": {"componentVersion": "'"$NEXT_VERSION"'"}}'`
  fi
  FINAL_CONFIG_JSON='{"components":'$NEW_CONFIG_JSON'}'
  #echo $FINAL_CONFIG_JSON
  echo $(echo "$FINAL_CONFIG_JSON" | jq '.') > ${DEPLOY_FILE_ARG}
  cat ${DEPLOY_FILE_ARG} | jq
}

_deploy_configuration_on_devices() 
{
  echo "ARN is in deployment : ${ARN}"
  CONFIG_FILE_ARG=$1
  CONFIG_URI="fileb://${CONFIG_FILE_ARG}"
  #THING_GROUP_ARN="arn:aws:iot:${AWS_REGION}:${AWS_ACCOUNT_NUM}:thinggroup/${DEV_IOT_THING_GROUP}"
  THING_ARN="arn:aws:iot:${AWS_REGION}:${AWS_ACCOUNT_NUM}:thing/${DEV_IOT_THING}"
  #aws greengrassv2 create-deployment --target-arn "arn:aws:iot:us-east-1:1233123123:thinggroup/ggv2-arm-tc-apps-ec2-group" --cli-input-json file://deployment_configuration.json --region us-east-1
  RES=`${AWS} greengrassv2 create-deployment --target-arn ${THING_ARN} --cli-input-json ${CONFIG_URI} --region ${AWS_REGION} --deployment-policies failureHandlingPolicy=DO_NOTHING`
  echo ${RES}
}

_updateTheVersionInFileInS3() 
{
  echo "Updating the version in the file."
  echo ${NEXT_VERSION} > ${CURRENT_VERSION_FILE}
  cat ${CURRENT_VERSION_FILE}
  aws s3 cp ${CURRENT_VERSION_FILE} ${S3_PATH}/${CURRENT_VERSION_FILE}
}

########################## MAIN ###############################
#
###############################################################
echo $#
if [ "$#" -ne 2 ]; then
  echo "usage: ddeploy-mqtt-connector.sh <IOT_THING_GROUP> <AWS_ACCOUNT_NUMBER>"
  echo $#
  exit 1
fi

#DEV_IOT_THING_GROUP=${1}
DEV_IOT_THING=${1}
AWS_ACCOUNT_NUMBER=${2}

include_public_comps=true
_setEnv
#_exportAWSCreds
_installSigil
_check_if_jq_exists
_checkIfABucketWithPrefixExists
_prepare_deployment_config_file_based_on_deployment_name ${DEPLOYMENT_CONFIG_FILE} ${COMPONENT_NAME}

RECIPE_FILE_NAME="${COMPONENT_NAME}-${NEXT_VERSION}.yaml"
if [[ ! ${COMP_VERSION} = "" ]]; then
      PREVIOUS_RECIPE_FILE_NAME="${COMPONENT_NAME}-${COMP_VERSION}.yaml"
fi

if [[ ! ${EXITING_COMP_VERSION} = "" ]]; then
      PREVIOUS_RECIPE_FILE_NAME="${COMPONENT_NAME}-${EXITING_COMP_VERSION}.yaml"
fi

echo ${COMPONENT_NAME}
echo ${NEXT_VERSION}
echo ${SRC_FOLDER}
echo ${RECIPE_FILE_NAME}

## Removing old recipe file from the local disk
if test -f "${PREVIOUS_RECIPE_FILE_NAME}"; then
    echo "Previous version recipe file : ${PREVIOUS_RECIPE_FILE_NAME} exists. Removing it from local disk."
    rm ${PREVIOUS_RECIPE_FILE_NAME}
fi

_compressArtifactsAndPushToCloud ${SRC_FOLDER} ${ARTIFACTS_ARCHIVE_FILE_NAME}

sigil -p -f recipe-file-template.yaml s3_path=${S3_PATH} \
    next_version=${NEXT_VERSION} \
    component_name=$COMPONENT_NAME \
    component_version_number=${NEXT_VERSION} \
    artifacts_zip_file_name=${ARTIFACTS_ARCHIVE_FILE_NAME} \
    artifacts_entry_file=${MAIN_ARTIFACT_FILE} > ${RECIPE_FILE_NAME}

echo "======== Generated recipe file is : ========"
cat ${RECIPE_FILE_NAME}
echo "======== End of recipe file : =============="
_create_gg_component_in_cloud ${RECIPE_FILE_NAME}
_deploy_configuration_on_devices ${DEPLOYMENT_CONFIG_FILE}