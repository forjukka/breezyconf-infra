from aws_cdk import (
    Stack,
    aws_ec2 as ec2
)
from constructs import Construct

class VpcStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        provider = ec2.NatProvider.instance_v2(
            instance_type=ec2.InstanceType("t4g.micro"),
            default_allowed_traffic=ec2.NatTrafficDirection.OUTBOUND_ONLY
        )

        vpc = ec2.Vpc(self, "Vpc",
            vpc_name="colordrops-vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.11.0.0/16"),
            availability_zones=["eu-west-1a", "eu-west-1b", "eu-west-1c"],
            nat_gateway_provider=provider,
            nat_gateways=1,
        )

        vpc.add_gateway_endpoint("S3Gateway", service=ec2.GatewayVpcEndpointAwsService.S3)
