import aws_cdk as core
import aws_cdk.assertions as assertions

from sm_studio_cdk_python.sm_studio_cdk_python_stack import SmStudioCdkPythonStack

# example tests. To run these tests, uncomment this file along with the example
# resource in sm_studio_cdk_python/sm_studio_cdk_python_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SmStudioCdkPythonStack(app, "sm-studio-cdk-python")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
