#!/usr/bin/env python3
import os

import aws_cdk as cdk

from breezyconf_infra.vpc_stack import VpcStack
from breezyconf_infra.eks_stack import EksStack
from breezyconf_infra.eks_addon_stack import EksAddonStack

app = cdk.App()

# For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html

VpcStack = VpcStack(app, "VpcStack",
    env=cdk.Environment(account='200562504897', region='eu-west-1') # change to match your account and region
)
EksStack = EksStack(app, "EksStack",
    env=cdk.Environment(account='200562504897', region='eu-west-1'), # change to match your account and region
    vpc=VpcStack.vpc
)
EksAddonStack = EksAddonStack(app, "EksAddonStack",
    env=cdk.Environment(account='200562504897', region='eu-west-1'), # change to match your account and region
    cluster=EksStack.cluster
)

app.synth()
