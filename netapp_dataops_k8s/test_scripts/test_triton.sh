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

printf "NetApp DataOps Toolkit for Kubernetes - Interactive test script\n\n"

printf "Prerequisites:\n"
printf "2 namespaces: default, dsk-test\n"
printf "1 server name that is required for NVIDIA Triton Inference Server instance"
printf "2 PVCs that already exists with the model repo named 'model-repo-test' and 'model-repo-test1' (1 PVC in each namespace) and model repo's loaded.\n"
proceed_prompt

##################################################
# Test class B - NVIDID Triton Inference Server management #
##################################################
printf "\n* Starting: Test class B - NVIDIA Triton Inference Server management\n\n"

##################################################
## Test set B.1. - default namespace, long opts ##
##################################################
printf "** Starting: Test set B.1. - default namespace, long opts\n\n"

### Create workspace 1
server1_name="b-1-w1"
model_pvc="model-repo-test"
command="./netapp_dataops_k8s_cli.py create triton-server --server-name=$server1_name --model-repo-pvc-name=$model_pvc"
echo "Running: $command"
eval $command
printf "\n"
kubectl get deployment ntap-dsutil-triton-$server1_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Create workspace 2
server2_name="b-1-w2"
model_pvc="model-repo-test"
command="./netapp_dataops_k8s_cli.py create triton-server --server-name=$server2_name --model-repo-pvc-name=$model_pvc --image=nvcr.io/nvidia/tritonserver:21.11-py3 --memory=512Mi --cpu=0.25"
echo "Running: $command"
eval $command
printf "\n"
kubectl get deployment ntap-dsutil-triton-$server2_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Use List to check if the servers still exist in default namespace
command="./netapp_dataops_k8s_cli.py list triton-servers"
echo "Running: $command"
eval $command
printf "\nRetrieving server:\n"
printf "\n"
proceed_prompt
printf "\n"

### Delete Triton Inference instance 1
command="./netapp_dataops_k8s_cli.py delete triton-server --server-name=$server1_name --force"
echo "Running: $command"
eval $command
printf "\nRetrieving server:\n"
kubectl get deployment ntap-dsutil-triton-$server1_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Delete Triton Inference instance 2
command="./netapp_dataops_k8s_cli.py delete triton-server --server-name=$server2_name --force"
echo "Running: $command"
eval $command
printf "\nRetrieving server:\n"
kubectl get deployment ntap-dsutil-triton-$server2_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

####################################################
## Test set B.2. - dsk-test namespace, long opts ##
####################################################
printf "** Starting: Test set B.2. - dsk-test namespace, long opts\n\n"
namespace="dsk-test"

### Create workspace 1
server3_name="b-2-w1"
model_pvc="model-repo-test1"
namespace="dsk-test"
command="./netapp_dataops_k8s_cli.py create triton-server --namespace=$namespace --server-name=$server3_name --model-repo-pvc-name=$model_pvc"
echo "Running: $command"
eval $command
printf "\n"
kubectl -n $namespace get deployment ntap-dsutil-triton-$server3_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Create workspace 2
server4_name="b-2-w2"
model_pvc="model-repo-test1"
namespace="dsk-test"
command="./netapp_dataops_k8s_cli.py create triton-server --namespace=$namespace --server-name=$server4_name --model-repo-pvc-name=$model_pvc --image=nvcr.io/nvidia/tritonserver:21.11-py3 --memory=512Mi --cpu=0.25 --load-balancer"
echo "Running: $command"
eval $command
printf "\n"
kubectl -n $namespace get deployment ntap-dsutil-triton-$server4_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Use List to check if the servers still exist in namespace: "dsk-test"
command="./netapp_dataops_k8s_cli.py list triton-servers --namespace=$namespace"
echo "Running: $command"
eval $command
printf "\nRetrieving server:\n"
printf "\n"
proceed_prompt
printf "\n"

### Delete Triton Inference instance 3
command="./netapp_dataops_k8s_cli.py delete triton-server --server-name=$server3_name --namespace=$namespace --force"
echo "Running: $command"
eval $command
printf "\nRetrieving server:\n"
kubectl -n $namespace get deployment ntap-dsutil-triton-$server3_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Delete Triton Inference instance 4
command="./netapp_dataops_k8s_cli.py delete triton-server --server-name=$server4_name --namespace=$namespace --force"
echo "Running: $command"
eval $command
printf "\nRetrieving server:\n"
kubectl -n $namespace get deployment ntap-dsutil-triton-$server4_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

#####################################################
## Test set B.3. - dsk-test namespace, short opts ##
#####################################################
printf "** Starting: Test set B.3. - dsk-test namespace, short opts\n\n"
namespace="dsk-test"

### Create workspace 1
server5_name="b-3-w1"
model_pvc="model-repo-test1"
namespace="dsk-test"
command="./netapp_dataops_k8s_cli.py create triton-server -n $namespace -s $server5_name -v $model_pvc"
echo "Running: $command"
eval $command
printf "\n"
kubectl -n $namespace get deployment ntap-dsutil-triton-$server5_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Create workspace 2
server6_name="b-3-w2"
model_pvc="model-repo-test1"
namespace="dsk-test"
command="./netapp_dataops_k8s_cli.py create triton-server -n $namespace -s $server6_name -v $model_pvc -i nvcr.io/nvidia/tritonserver:21.11-py3 -m 512Mi -p 0.25 -b"
echo "Running: $command"
eval $command
printf "\n"
kubectl -n $namespace get deployment ntap-dsutil-triton-$server6_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Use List to check if the servers still exist in namespace: "dsk-test"
command="./netapp_dataops_k8s_cli.py list triton-servers --namespace=$namespace"
echo "Running: $command"
eval $command
printf "\nRetrieving server:\n"
printf "\n"
proceed_prompt
printf "\n"

### Delete Triton Inference instance 5
command="./netapp_dataops_k8s_cli.py delete triton-server --server-name=$server5_name --namespace=$namespace --force"
echo "Running: $command"
eval $command
printf "\nRetrieving server:\n"
kubectl -n $namespace get deployment ntap-dsutil-triton-$server5_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

### Delete Triton Inference instance 6
command="./netapp_dataops_k8s_cli.py delete triton-server --server-name=$server6_name --namespace=$namespace --force"
echo "Running: $command"
eval $command
printf "\nRetrieving server:\n"
kubectl -n $namespace get deployment ntap-dsutil-triton-$server6_name -o yaml
printf "\n"
proceed_prompt
printf "\n"

###################################
printf "* Test class B complete!\n"
