from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_eks as eks,
)
from constructs import Construct

class EksAddonStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, cluster: eks.ICluster, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Install only necessary addons here before ArgoCD takes over deployments

        cluster.add_helm_chart("ArgoCD",
            chart="argo-cd",
            release="argo-cd",
            repository="https://argoproj.github.io/argo-helm",
            namespace="argocd",
            values={
                "ingress.enabled": "true",
                "ingressClassName": "alb",
                "ingress.controller": "aws",
                "ingress.annotations": {
                    "kubernetes.io/ingress.class": "alb",
                    "alb.ingress.kubernetes.io/scheme": "internet-facing",
                    "alb.ingress.kubernetes.io/target-type": "ip",
                    "alb.ingress.kubernetes.io/listen-ports": '[{"HTTPS":80}]',
                },
                "aws.serviceType": "ClusterIP"
            }
        )

        cluster.add_helm_chart("AWSLoadBalancerController",
            chart="aws-load-balancer-controller",
            release="aws-load-balancer-controller",
            repository="https://aws.github.io/eks-charts",
            namespace="kube-system",
            values={
                "clusterName": "breezyconf-cluster",
                "serviceAccount.create": "false",
                "serviceAccount.name": "aws-load-balancer-controller",
                "region": self.region,
                "vpcId": cluster.vpc.vpc_id
            }
        )
