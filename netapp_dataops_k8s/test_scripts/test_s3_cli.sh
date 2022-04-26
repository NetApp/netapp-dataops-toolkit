#!/usr/bin/env bash

proceed_prompt () {
    while true; do
        read -p "Are you ready to proceed (y/n)? " proceed
        case $proceed in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) printf "Invalid entry\n";;
        esac
    done
}

print_configuration_help() {
    printf "\n"
    printf "To configure this test script create a file named s3_cli_config with the following shell variables set."
    printf "\n\n"
    printf "cli_path=VALUE            # The path to the cli script. Used for testing in development environment. Use empty string if you don't want to set a specific path.\n"
    printf "test_secret_name=VALUE    # The name of the K8s secret used by the test\n"
    printf "s3_access_key=VALUE       # The S3 access key\n"
    printf "s3_secret_key=VALUE       # The S3 secret key\n"
    printf "root_ca_cert_path=VALUE   # The path to a valid root ca certificate file\n"
    printf "inter_ca_cert_path=VALUE  # The path to an intermediate ca certificate file. This file may not need to be valid?\n"
    printf "s3_host=VALUE             # The hostname or IP address of the S3 service\n"
    printf "s3_port=VALUE             # The port number the S3 service is listening on\n"
    printf "s3_protocol=VALUE         # The protocol to use. Either http or https\n"
    printf "target_pvc=VALUE          # The name of a pvc to use for getting files from S3\n"
    printf "source_bucket=VALUE       # The name of a bucket with data to use to get data from S3\n"
    printf "source_object=VALUE        # The name of an object to copy from the source bucket\n"
    printf "target_bucket=VALUE       # The name of a bucket to copy files to\n"
    printf "alt_namespace=VALUE       # The name of an alternate namespace to use. This should be created before running this script.\n"

    exit
}

printf "NetApp DataOps Toolkit for Kubernetes - Interactive test script\n\n"

printf "Prerequisites:\n"
printf "  * 2 namespaces: default plus one manually defined namespace (configured in s3_cli_config)\n"
printf "  * Environment configuration file s3_cli_config\n"
printf "  * Have an S3 service with https enabled available\n"
printf "  * Have a bucket with data in it available in S3\n"
printf "  * Have an empty bucket available in S3 (to verify PUTs)\n"
printf "  * Have a PVC with data in it (for PUTs) (both namespaces)\n"
printf "  * Have an empty PVC available (for GETs) (both namespaces)\n"
printf ""
proceed_prompt

# Source PVC Setup instructions
# 1. Create a PVC in the cluster named dataops-test-source-pvc
# 2. Apply the following yaml to create a pod to generate files on the pvc
# apiVersion: v1
# kind: Pod
# metadata:
#   name: dataops-test-create-volumedata
#   namespace: default
# spec:
#   containers:
#     - name: dataops-test-create-pod
#       image: busybox:stable-musl
#       volumeMounts:
#         - name: dataops-test-volume
#           mountPath: /mnt/data
#       command: ["sh"]
#       args: ["-c", "echo 'file1' > /mnt/data/one.txt;echo 'file2' > /mnt/data/two.txt;mkdir /mnt/data/layer2;mkdir /mnt/data/layer2/layer3;echo 'file3' > /mnt/data/layer2/three.txt;echo 'file4' > /mnt/data/layer2/layer3/four.txt"]
#   volumes:
#     - name: dataops-test-volume
#       persistentVolumeClaim:
#         claimName: dataops-test-source-pvc
#   restartPolicy: Never

###############################################
# Test class D - Data Movement                #
###############################################
printf "\n* Starting: Test class D - Data Movement (S3)\n\n"

printf "\n* Checking for Test Configuration File s3_cli_config...\n"
if [ -f "s3_cli_config" ]
then
    . s3_cli_config

    [ ! -v "cli_path" ] && print_configuration_help
    [ ! -v "test_secret_name" ] && print_configuration_help
    [ ! -v "s3_access_key" ] && print_configuration_help
    [ ! -v "s3_secret_key" ] && print_configuration_help
    [ ! -v "root_ca_cert_path" ] && print_configuration_help
    [ ! -v "s3_host" ] && print_configuration_help
    [ ! -v "s3_port" ] && print_configuration_help
    [ ! -v "s3_protocol" ] && print_configuration_help
    [ ! -v "target_pvc" ] && printf " Missing target_pvc\n" && print_configuration_help
    [ ! -v "source_bucket" ] && printf " Missing source_bucket\n" && print_configuration_help
    [ ! -v "source_object" ] && printf " Missing source_object\n" && print_configuration_help
    [ ! -v "target_bucket" ] && printf " Missing target_bucket\n" && print_configuration_help
    [ ! -v "alt_namespace" ] && printf " Missing alt_namespace\n" && print_configuration_help

else
  print_configuration_help
fi

##################################################
## Test set D.1. - default namespace, long opts ##
##################################################
printf "** Starting: Test set D.1. - default namespace, long opts\n\n"

# These are variables we don't need the user to set
primary_ca_map_name="datops-s3-root-ca-map"
source_pvc="dataops-test-source-pvc"
image_name="minio/mc:RELEASE.2021-06-13T17-48-22Z"

# Determine if we need to use HTTPS or not
# Initially assume yes. We can add logic to determine this if needed.
protocol_flag="--use-https"

### Create a secret
printf "\n*** Testing the create s3-secret command ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py create s3-secret --secret-name=$test_secret_name --access-key=$s3_access_key --secret-key=$s3_secret_key"
echo "Running: $command"
eval $command
printf "\nRetrieving secret:\n"
kubectl get secret $test_secret_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Create a CA Config Map
printf "\n*** Testing the create ca-config-map command ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py create ca-config-map --config-map-name=$primary_ca_map_name --file=$root_ca_cert_path"
echo "Running: $command"
eval $command
printf "\nRetrieving the config map:\n"
kubectl get configmaps $primary_ca_map_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Test get-s3 bucket
printf "\n*** Testing the get-s3 bucket command ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py get-s3 bucket --credentials-secret=$test_secret_name --s3-host=$s3_host --bucket-name=$source_bucket --pvc-name=$target_pvc --s3-port=$s3_port $protocol_flag"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
kubectl get job -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Test getting the job status
printf "\n*** Testing show s3-job command ***\n"
read -p "Enter the job name: " job_name
command="${cli_path}netapp_dataops_k8s_cli.py show s3-job --job=$job_name"
echo "Running: $command"
eval $command
printf "\n"
proceed_prompt
printf "\n"

### Test deleting the job
printf "\n*** Testing the delete s3-job command ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job --job=$job_name"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"

### Test get-s3 object
printf "\n*** Testing get-s3 object command ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py get-s3 object --credentials-secret=$test_secret_name --s3-host=$s3_host --bucket-name=$source_bucket --pvc-name=$target_pvc --s3-port=$s3_port $protocol_flag --object-key=$source_object"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
sleep 2
kubectl get job -o yaml
read -p "Enter the job name: " transfer_job
printf "Here are the pods associated with the job.\n"
kubectl get pods --selector=job-name=$transfer_job
read -p "Enter a pod  name: " pod_name
printf "\nShow the job logs for $pod_name"
kubectl logs $pod_name
printf "\n"
proceed_prompt
printf "\n"


### Cleanup get-s3 object job
printf "\nCleanup job for get-s3 object command"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job --job=$transfer_job"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"


### Test put-s3 object 
printf "\n*** Testing the put-s3 object command ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py put-s3 object --credentials-secret=$test_secret_name --s3-host=$s3_host --bucket-name=$target_bucket --pvc-name=$source_pvc --s3-port=$s3_port $protocol_flag --object-key=one.txt --file-location=one.txt"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
kubectl get job -o yaml
read -p "Enter the job name: " transfer_job
printf "Here are the pods associated with the job.\n"
kubectl get pods --selector=job-name=$transfer_job
read -p "Enter a pod  name: " pod_name
printf "\nShow the job logs for $pod_name"
kubectl logs $pod_name
printf "\n"
proceed_prompt
printf "\n"

### Cleanup put-s3 object job
printf "\nCleanup job for put-s3 object command"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job --job=$transfer_job"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"

### Test put-s3 bucket 
printf "\n*** Testing the put-s3 bucket command ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py put-s3 bucket --credentials-secret=$test_secret_name --s3-host=$s3_host --bucket-name=$target_bucket --pvc-name=$source_pvc --s3-port=$s3_port $protocol_flag"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
kubectl get job -o yaml
read -p "Enter the job name: " transfer_job
printf "Here are the pods associated with the job.\n"
kubectl get pods --selector=job-name=$transfer_job
read -p "Enter a pod  name: " pod_name
printf "\nShow the job logs for $pod_name"
kubectl logs $pod_name
printf "\n"
proceed_prompt
printf "\n"

### Cleanup put-s3 bucket job
printf "\nCleanup job for put-s3 bucket command"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job --job=$transfer_job"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"

### Test delete ca-config-map
printf "\n*** Testing the delete ca-config-map command ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py delete ca-config-map --config-map-name=$primary_ca_map_name"
echo "Running: $command"
eval $command
printf "\nRetrieving the config map:\n"
kubectl get configmaps $primary_ca_map_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Test delete s3-secret
printf "\n*** Testing the delete s3-secret command ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-secret --secret-name=$test_secret_name"
echo "Running: $command"
eval $command
printf "\nRetrieving secret:\n"
kubectl get secret $test_secret_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

########################################################
## Test set D.2. - short opts, alternate namespace    ##
########################################################
printf "** Starting: Test set D.2. - testing short options and all options\n\n"

### Create a secret
printf "\n*** Testing the create s3-secret command with short options ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py create s3-secret -d $test_secret_name -a $s3_access_key -s $s3_secret_key -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nRetrieving secret:\n"
kubectl get secret $test_secret_name --namespace=$alt_namespace -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Create a CA Config Map
printf "\n*** Testing the create ca-config-map command with short options ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py create ca-config-map -c $primary_ca_map_name -f $root_ca_cert_path -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nRetrieving the config map:\n"
kubectl get configmaps $primary_ca_map_name --namespace=$alt_namespace -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Test get-s3 bucket
printf "\n*** Testing the get-s3 bucket command with short options ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py get-s3 bucket -c $test_secret_name -o $s3_host -b $source_bucket -p $target_pvc -t $s3_port $protocol_flag -v -m $primary_ca_map_name -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
kubectl get job --namespace=$alt_namespace -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Test getting the job status
printf "\n*** Testing show s3-job command with short options ***\n"
read -p "Enter the job name: " job_name
command="${cli_path}netapp_dataops_k8s_cli.py show s3-job -j $job_name -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\n"
proceed_prompt
printf "\n"

### Test deleting the job
printf "\n*** Testing the delete s3-job command with short options ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job -j $job_name -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job --namespace=$alt_namespace
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"

### Test get-s3 object
printf "\n*** Testing get-s3 object command with short options ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py get-s3 object -c $test_secret_name -o $s3_host -b $source_bucket -p $target_pvc -t $s3_port $protocol_flag -k $source_object -v -m $primary_ca_map_name -n $alt_namespace -f copied_file.txt"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
sleep 2
kubectl get job --namespace=$alt_namespace -o yaml
read -p "Enter the job name: " transfer_job
printf "Here are the pods associated with the job.\n"
kubectl get pods --namespace=$alt_namespace --selector=job-name=$transfer_job
read -p "Enter a pod  name: " pod_name
printf "\nShow the job logs for $pod_name"
kubectl logs --namespace=$alt_namespace $pod_name
printf "\n"
proceed_prompt
printf "\n"

### Cleanup get-s3 object job
printf "\nCleanup job for get-s3 object command"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job -j $transfer_job -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job --namespace=$alt_namespace
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"

### Test put-s3 object 
printf "\n*** Testing the put-s3 object command with short options ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py put-s3 object -c $test_secret_name -o $s3_host -b $target_bucket -p $source_pvc -t $s3_port $protocol_flag -k one.txt -f one.txt -v -m $primary_ca_map_name -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
kubectl get job --namespace=$alt_namespace -o yaml
read -p "Enter the job name: " transfer_job
printf "Here are the pods associated with the job.\n"
kubectl get pods --namespace=$alt_namespace --selector=job-name=$transfer_job
read -p "Enter a pod  name: " pod_name
printf "\nShow the job logs for $pod_name"
kubectl logs --namespace=$alt_namespace $pod_name
printf "\n"
proceed_prompt
printf "\n"

### Cleanup put-s3 object job
printf "\nCleanup job for put-s3 object command"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job -j $transfer_job -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job --namespace=$alt_namespace
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"

### Test put-s3 bucket 
printf "\n*** Testing the put-s3 bucket command with short options ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py put-s3 bucket -c $test_secret_name -o $s3_host -b $target_bucket -p $source_pvc -t $s3_port $protocol_flag -v -m $primary_ca_map_name -n $alt_namespace -d layer2"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
kubectl get job --namespace=$alt_namespace -o yaml
read -p "Enter the job name: " transfer_job
printf "Here are the pods associated with the job.\n"
kubectl get pods --namespace=$alt_namespace --selector=job-name=$transfer_job
read -p "Enter a pod  name: " pod_name
printf "\nShow the job logs for $pod_name"
kubectl logs --namespace=$alt_namespace $pod_name
printf "\n"
proceed_prompt
printf "\n"

### Cleanup put-s3 bucket job
printf "\nCleanup job for put-s3 bucket command"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job -j $transfer_job -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job --namespace=$alt_namespace
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"

########################################################
## Test set D.3. - miscellaneous options              ##
########################################################
printf "** Starting: Test set D.3. - testing miscellaneous options\n\n"

# Set resource variables
requested_memory="8000Ki"
requested_cpu="300m"
limit_memory="50000Ki"
limit_cpu="500m"

### Test get-s3 bucket with image and resource limits
printf "\n*** Testing the get-s3 bucket command with extra options ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py get-s3 bucket -c $test_secret_name -o $s3_host -b $source_bucket -p $target_pvc -t $s3_port $protocol_flag -n $alt_namespace -i $image_name --cpu-request=$requested_cpu --cpu-limit=$limit_cpu --memory-request=$requested_memory --memory-limit=$limit_memory"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
kubectl get job --namespace=$alt_namespace -o yaml
read -p "Enter the job name: " transfer_job
printf "Here are the pods associated with the job.\n"
kubectl get pods --namespace=$alt_namespace --selector=job-name=$transfer_job
read -p "Enter a pod  name: " pod_name
printf "\nShow the job logs for $pod_name"
kubectl logs --namespace=$alt_namespace $pod_name
printf "\n"
proceed_prompt
printf "\n"

### Cleanup get-s3 bucket job
printf "\nCleanup job for get-s3 bucket command\n"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job -j $transfer_job -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job --namespace=$alt_namespace
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"

### Test get-s3 object
printf "\n*** Testing get-s3 object command with extra options ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py get-s3 object -c $test_secret_name -o $s3_host -b $source_bucket -p $target_pvc -t $s3_port $protocol_flag -k $source_object -n $alt_namespace -i $image_name --cpu-request=$requested_cpu --cpu-limit=$limit_cpu --memory-request=$requested_memory --memory-limit=$limit_memory"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
sleep 2
kubectl get job --namespace=$alt_namespace -o yaml
read -p "Enter the job name: " transfer_job
printf "Here are the pods associated with the job.\n"
kubectl get pods --namespace=$alt_namespace --selector=job-name=$transfer_job
read -p "Enter a pod  name: " pod_name
printf "\nShow the job logs for $pod_name"
kubectl logs --namespace=$alt_namespace $pod_name
printf "\n"
proceed_prompt
printf "\n"

### Cleanup get-s3 object job
printf "\nCleanup job for get-s3 object command\n"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job -j $transfer_job -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job --namespace=$alt_namespace
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"

### Test put-s3 object 
printf "\n*** Testing the put-s3 object command with extra options ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py put-s3 object -c $test_secret_name -o $s3_host -b $target_bucket -p $source_pvc -t $s3_port $protocol_flag -k one.txt -f one.txt -n $alt_namespace -i $image_name --cpu-request=$requested_cpu --cpu-limit=$limit_cpu --memory-request=$requested_memory --memory-limit=$limit_memory"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
kubectl get job --namespace=$alt_namespace -o yaml
read -p "Enter the job name: " transfer_job
printf "Here are the pods associated with the job.\n"
kubectl get pods --namespace=$alt_namespace --selector=job-name=$transfer_job
read -p "Enter a pod  name: " pod_name
printf "\nShow the job logs for $pod_name"
kubectl logs --namespace=$alt_namespace $pod_name
printf "\n"
proceed_prompt
printf "\n"

### Cleanup put-s3 object job
printf "\nCleanup job for put-s3 object command\n"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job -j $transfer_job -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job --namespace=$alt_namespace
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"

### Test put-s3 bucket 
printf "\n*** Testing the put-s3 bucket command with extra options ***\n"
command="${cli_path}netapp_dataops_k8s_cli.py put-s3 bucket -c $test_secret_name -o $s3_host -b $target_bucket -p $source_pvc -t $s3_port $protocol_flag -n $alt_namespace -i $image_name --cpu-request=$requested_cpu --cpu-limit=$limit_cpu --memory-request=$requested_memory --memory-limit=$limit_memory"
echo "Running: $command"
eval $command
printf "\nChecking the existing jobs:\n"
kubectl get job --namespace=$alt_namespace -o yaml
read -p "Enter the job name: " transfer_job
printf "Here are the pods associated with the job.\n"
kubectl get pods --namespace=$alt_namespace --selector=job-name=$transfer_job
read -p "Enter a pod  name: " pod_name
printf "\nShow the job logs for $pod_name"
kubectl logs --namespace=$alt_namespace $pod_name
printf "\n"
proceed_prompt
printf "\n"

### Cleanup put-s3 bucket job
printf "\nCleanup job for put-s3 bucket command\n"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-job -j $transfer_job -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nChecking existing jobs after 5 seconds:\n"
sleep 5
kubectl get job --namespace=$alt_namespace
printf "If the job still shows up try checking for the job in another window for awhile to see if it goes away."
printf "\n"
proceed_prompt
printf "\n"

### Test delete ca-config-map
printf "\n*** Testing the delete ca-config-map command with short options***\n"
command="${cli_path}netapp_dataops_k8s_cli.py delete ca-config-map -c $primary_ca_map_name -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nRetrieving the config map:\n"
kubectl get configmaps $primary_ca_map_name --namespace=$alt_namespace -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Test delete s3-secret
printf "\n*** Testing the delete s3-secret command with short options***\n"
command="${cli_path}netapp_dataops_k8s_cli.py delete s3-secret -d $test_secret_name -n $alt_namespace"
echo "Running: $command"
eval $command
printf "\nRetrieving secret:\n"
kubectl get secret $test_secret_name --namespace=$alt_namespace -o yaml
printf "\n"
proceed_prompt
printf "\n"

