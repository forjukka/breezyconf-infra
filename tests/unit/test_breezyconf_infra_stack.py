import aws_cdk as core
import aws_cdk.assertions as assertions

from breezyconf_infra.breezyconf_infra_stack import BreezyconfInfraStack

# example tests. To run these tests, uncomment this file along with the example
# resource in breezyconf_infra/breezyconf_infra_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = BreezyconfInfraStack(app, "breezyconf-infra")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
