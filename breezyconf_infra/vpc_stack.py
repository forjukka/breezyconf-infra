from aws_cdk import (
    Stack,
    Tags,
    aws_ec2 as ec2,
    aws_ssm as ssm
)
from constructs import Construct

class VpcStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        self.vpc = ec2.Vpc(self, "Vpc",
            vpc_name="breezyconf-vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.11.0.0/16"),
            availability_zones=["eu-west-1a", "eu-west-1b", "eu-west-1c"],
            nat_gateways=1, # change to 3 in production
        )

        # Tag public subnets
        for subnet in self.vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnets:
            Tags.of(subnet).add("kubernetes.io/role/elb", "1")

        # Tag private subnets
        for subnet in self.vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets:
            Tags.of(subnet).add("kubernetes.io/role/internal-elb", "1")