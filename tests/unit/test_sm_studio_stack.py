import aws_cdk as core
import aws_cdk.assertions as assertions

from sm_studio.sm_studio_stack import SmStudioStack

# example tests. To run these tests, uncomment this file along with the example
# resource in sm_studio/sm_studio_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SmStudioStack(app, "sm-studio")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
