#!/usr/bin/env python3
import os

import aws_cdk as cdk

from breezyconf_infra.vpc_stack import VpcStack
from breezyconf_infra.eks_stack import EksStack
from breezyconf_infra.eks_addon_stack import EksAddonStack
from breezyconf_infra.app_stack import AppStack

app = cdk.App()

# For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
# change the below environments to match your account and region

VpcStack = VpcStack(app, "VpcStack",
    env=cdk.Environment(account='200562504897', region='eu-west-1')
)
EksStack = EksStack(app, "EksStack",
    env=cdk.Environment(account='200562504897', region='eu-west-1'),
    vpc=VpcStack.vpc
)
EksAddonStack = EksAddonStack(app, "EksAddonStack",
    env=cdk.Environment(account='200562504897', region='eu-west-1'),
    cluster=EksStack.cluster
)
AppStack = AppStack(app, "AppStack",
    env=cdk.Environment(account='200562504897', region='eu-west-1'),
    vpc=VpcStack.vpc,
    cluster=EksStack.cluster
)

app.synth()
