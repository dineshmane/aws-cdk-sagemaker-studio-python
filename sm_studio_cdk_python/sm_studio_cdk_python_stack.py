from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_sagemaker as sagemaker,
    CfnOutput,
    aws_lambda as _lambda,
    aws_logs
)
import json
from aws_cdk import aws_lambda_python_alpha as _alambda
from constructs import Construct
import json
from aws_cdk.custom_resources import Provider
import aws_cdk as core
from constructs import Construct
from cdk_nag import NagSuppressions

class SmStudioCdkPythonStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        file = open("project_config.json")
        variables = json.load(file)
        stack_name = Stack.of(self).stack_name.lower()

        # Create Studio Role
        role = iam.Role(
            self,
            "Studio Role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
            ],
            inline_policies={
                "CustomRules": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "codewhisperer:GenerateRecommendations*",
                            ],
                            resources=["*"],
                        )
                    ]
                )
            },
        )

        vpc = ec2.Vpc(self, "VPC")

        self.public_subnet_ids = [
            public_subnet.subnet_id for public_subnet in vpc.public_subnets
        ]

        flow_log_group = aws_logs.LogGroup(self, "vpcFlowLogGroup")

        flow_log_role = iam.Role(self, 
                                "vpcFLowLogRole",
                                assumed_by=iam.ServicePrincipal("vpc-flow-logs.amazonaws.com")
                                )

        ec2.FlowLog(self, "FlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(flow_log_group, flow_log_role)
        )

        # Open file then code into base 64 then decode into utf-8
        # setup_script = open(
        #     "sm_studio_cdk_python/scripts/shell/on-jupyter-server-start.sh", "rb"
        # )
        # setup_script_b64 = base64.b64encode(setup_script.read()).decode("utf-8")
        # setup_script_name = f"setup-{stack_name}"
        # # Create lambda function to call sdk to either create or delete lifecycle config
        # setup = cr.AwsCustomResource(
        #     self,
        #     "SetupLifecycle",
        #     timeout=Duration.seconds(10),
        #     on_create=cr.AwsSdkCall(
        #         service="SageMaker",
        #         action="createStudioLifecycleConfig",
        #         parameters={
        #             "StudioLifecycleConfigAppType": "JupyterServer",
        #             "StudioLifecycleConfigContent": setup_script_b64,
        #             "StudioLifecycleConfigName": setup_script_name,
        #         },
        #         physical_resource_id=cr.PhysicalResourceId.of("create_lifecycle"),
        #     ),
        #     on_update=cr.AwsSdkCall(
        #         service="SageMaker",
        #         action="describeStudioLifecycleConfig",
        #         parameters={
        #             "StudioLifecycleConfigName": setup_script_name,
        #         },
        #         output_paths=["StudioLifecycleConfigArn"],
        #         physical_resource_id=cr.PhysicalResourceId.of("update_lifecycle"),
        #     ),
        #     on_delete=cr.AwsSdkCall(
        #         service="SageMaker",
        #         action="deleteStudioLifecycleConfig",
        #         parameters={
        #             "StudioLifecycleConfigName": setup_script_name,
        #         },
        #         physical_resource_id=cr.PhysicalResourceId.of("delete_lifecycle"),
        #     ),
        #     policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
        #         resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
        #     ),
        # )

        # Create domain with IAM auth, role created above, VPC created above and subnets created above
        domain = sagemaker.CfnDomain(
            self,
            "Domain",
            auth_mode="IAM",
            default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=role.role_arn,
                ## Automatically shut down idle kernels
                # jupyter_server_app_settings=sagemaker.CfnDomain.JupyterServerAppSettingsProperty(
                #     default_resource_spec=sagemaker.CfnDomain.ResourceSpecProperty(
                #         lifecycle_config_arn=setup.get_response_field(
                #             "StudioLifecycleConfigArn"
                #         ),
                #     )
                # ),
            ),
            domain_name=f"Studio-{stack_name}",
            subnet_ids=self.public_subnet_ids,
            vpc_id=vpc.vpc_id,
        )

        # # Assign lifecycle to domain via SDK call
        # cr.AwsCustomResource(
        #     self,
        #     "Add Lifecycles to Domain",
        #     on_create=cr.AwsSdkCall(
        #         service="SageMaker",
        #         action="updateDomain",
        #         parameters={
        #             "DomainId": domain.attr_domain_id,
        #             "DefaultUserSettings": {
        #                 "JupyterServerAppSettings": {
        #                     "LifecycleConfigArns": [
        #                         setup.get_response_field("StudioLifecycleConfigArn"),
        #                     ]
        #                 }
        #             },
        #         },
        #         physical_resource_id=cr.PhysicalResourceId.of("add_lifecycle_to_domain"),
        #     ),
        #     policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
        #         resources=[domain.attr_domain_arn]
        #     ),
        # )
        
        #Create the Custom Resource to enable sagemaker projects for the different personas
        event_handler = _alambda.PythonFunction(
            self,
            "sg-project-function",
            runtime=_lambda.Runtime.PYTHON_3_11,
            architecture=_lambda.Architecture.ARM_64,
            entry="./sm_studio_cdk_python/lambda/enable_sm_projects/",
            timeout=core.Duration.seconds(120),
        )
        event_handler.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sagemaker:EnableSagemakerServicecatalogPortfolio",
                    "servicecatalog:ListAcceptedPortfolioShares",
                    "servicecatalog:AssociatePrincipalWithPortfolio",
                    "servicecatalog:AcceptPortfolioShare",
                    "iam:GetRole",
                ],
                resources=["*"],
            ),
        )
        provider = Provider(self, "sg-project-lead-provider", on_event_handler=event_handler)

        core.CustomResource(
            self,
            "sg-project",
            service_token=provider.service_token,
            removal_policy=core.RemovalPolicy.DESTROY,
            resource_type="Custom::EnableSageMakerProjects",
            properties={
                "iteration": 1,
                "ExecutionRoles": [role.role_arn],
            },
        )
        # Create users using variables file
        if variables["SageMakerUserProfiles"]:
            for user in variables["SageMakerUserProfiles"]:
                sagemaker.CfnUserProfile(
                    self,
                    f"User-{user}",
                    domain_id=domain.attr_domain_id,
                    user_profile_name=user,
                    user_settings=sagemaker.CfnUserProfile.UserSettingsProperty(
                        execution_role=role.role_arn,
                    ),
                )

        CfnOutput(self, "domain_id", value=domain.attr_domain_id)
        
        # # CDK NAG suppression
        # NagSuppressions.add_resource_suppressions_by_path(            
        #     self,
        #     path="/SagemakerStudioSetupStack/AWS679f53fac002430cb0da5b7982bd2287/ServiceRole/Resource",
        #     suppressions = [
        #                     { "id": 'AwsSolutions-IAM4', "reason": 'Sagemaker Notebook policies need to be broad to allow access' },
        #                 ],
        #     apply_to_children=True
        # )

        ## CDK Nag Suppression
        NagSuppressions.add_resource_suppressions(self,
                            suppressions=[{
                                            "id": "AwsSolutions-IAM4",
                                            "reason": "Sagemaker Notebook policies need to be broad to allow access to ",
                                            },{
                                            "id": "AwsSolutions-IAM5",
                                            "reason": "SM Role requires access to all indicies",
                                            },
                                            {
                                            "id": "AwsSolutions-L1",
                                            "reason": "It is L1 construct, so we can't upgrade the runtime to the latest one.",
                                            },
                                            
                                        ],
                            apply_to_children=True)
        
      
        # ## CDK NAG suppression
        # NagSuppressions.add_resource_suppressions_by_path(self,       
        #             path="/MlOpsPrototypeStack/Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C/Resource",
        #             suppressions = [
        #                             { "id": 'AwsSolutions-L1', "reason": 'CDK BucketDeployment L1 Construct' },
        #                         ],
        #             apply_to_children=True
        #         )