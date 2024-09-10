# AWS Infrastructure for BreezyConf presentation

The purpose of this repo is to provision VPC and Amazon EKS cluster that can be used for application deployment.
The reason for having this infrastructure in a separate repo is to decouple it from apps that typically
see more rapid changes. Quite often there's also a separate DevOps team that manages infra and EKS clusters.

## About AWS CDK

CDK is a popular infrastructure-as-code tool that allows you to define AWS infrastructure with your favorite
programming language. We use python here. A CDK project consists of an App with one or more Stacks under it. 
In this project we have four separate stacks for separation of concerns (we don't want to put all eggs in the same basket).

## How to deploy

First install AWS CDK into your laptop according to CDK documentation:
https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html

Then run these commands:

```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt # install dependencies
aws sso login # if you are using IAM Identity Center
cdk diff # to verify and see that what will be deployed
cdk deploy VpcStack
cdk deploy EksStack
cdk deploy EksAddonStack
cdk deploy AppStack
```

After the EKS cluster has been deployed, you should update your kubeconfig
to be able to run kubectl against it:

```
aws eks update-kubeconfig --name breezyconf-cluster
kubectl config use-context arn:aws:eks:eu-west-1:ACCOUNT_ID:cluster/breezyconf-cluster
kubectl get nodes
```
