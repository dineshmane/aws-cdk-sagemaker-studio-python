#!/usr/bin/env python3
import json
import cdk_nag
from aws_cdk import Aspects
import aws_cdk as cdk

import aws_cdk as cdk

from sm_studio_cdk_python.sm_studio_cdk_python_stack import SmStudioCdkPythonStack

file = open("project_config.json")
variables = json.load(file)
main_stack_name = variables["MainStackName"]

app = cdk.App()

SmStudioCdkPythonStack(app, main_stack_name,)

Aspects.of(app).add(cdk_nag.AwsSolutionsChecks(reports=True, verbose=True))
app.synth()
