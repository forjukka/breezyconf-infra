# AWS Infrastructure for BreezyConf presentation

The purpose of this repo is to provision VPC and Amazon EKS cluster that can be used for application deployments.
The reason for having this core infrastructure in a separate repo is to decouple it from apps that typically
see more rapid changes. This model also supports a separate DevOps team that manages EKS clusters.
