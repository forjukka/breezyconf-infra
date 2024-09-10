from aws_cdk import (
    Stack,
    Size,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_eks as eks,
    aws_ecr as ecr
)
from constructs import Construct
from aws_cdk.lambda_layer_kubectl_v30 import KubectlV30Layer

class EksStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.IVpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        self.cluster = eks.Cluster(self, "MyCluster",
            vpc=vpc,
            vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)],
            cluster_name="breezyconf-cluster",
            version=eks.KubernetesVersion.V1_30,
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
            authentication_mode=eks.AuthenticationMode.API_AND_CONFIG_MAP,
            kubectl_layer=KubectlV30Layer(self, "kubectl"),
            kubectl_memory=Size.gibibytes(2),
            default_capacity=0,
        )

        # OIDC provider should be created automatically for the EKS cluster. If not, uncomment the following.
        #oidc_provider = eks.OpenIdConnectProvider(self, "OIDCProvider",
        #    url=self.cluster.cluster_open_id_connect_issuer_url
        #)

        self.cluster.add_nodegroup_capacity("breezyconf-ng2",
            instance_types=[ec2.InstanceType("t3.large")],
            ami_type=eks.NodegroupAmiType.AL2023_X86_64_STANDARD, # Use Amazon Linux 2023
            max_size=6,
            min_size=3,
            desired_size=3,
            nodegroup_name="breezyconf-ng2"
        )

        # IAM Identity Center role that you use to in this AWS account
        idc_role_arn = "arn:aws:iam::200562504897:role/aws-reserved/sso.amazonaws.com/eu-west-1/AWSReservedSSO_AWSAdministratorAccess_ded7ba96587fd595"

        # Add cluster access for the AWS Identity Center role
        self.cluster.grant_access("clusterAdminAccess", idc_role_arn, [
            eks.AccessPolicy.from_access_policy_name("AmazonEKSClusterAdminPolicy",
                access_scope_type=eks.AccessScopeType.CLUSTER
            )
        ])

        # Add ECR Private Repository
        repository = ecr.Repository(self, "BreezyRepo",
            image_scan_on_push=True,
            image_tag_mutability=ecr.TagMutability.IMMUTABLE
        )
        user = iam.User(self, "GitHubActionUser") # for production use GitHub OIDC provider
        repository.grant_push(user)
