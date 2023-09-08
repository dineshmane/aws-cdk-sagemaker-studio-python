from aws_cdk import (
    aws_ec2 as ec2,
    aws_sagemaker as sagemaker,
    aws_iam as iam,
    Stack
)

from constructs import Construct

class SmStudioStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

    # Create a SageMakerExecutionRole-${region}-cdk for the SageMaker Studio
        
        region = Stack.of(self).region
        account = Stack.of(self).account
        
        sagemaker_execution_role = iam.Role(
            self,
            "SageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            role_name=f"SageMakerExecutionRole-{region}-cdk",
            description="SageMaker execution role",
        )

        # Add AmazonSageMakerFullAccess and AmazonS3FullAccess to the role
        sagemaker_execution_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
        )

        sagemaker_execution_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )

        # Create a SageMakerUserSettings for the SageMaker Studio
        user_settings = {"executionRole": sagemaker_execution_role.role_arn}

        # Set a default VPC for the SageMaker Studio
        # default_vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True)
        vpc = ec2.Vpc(self, "VPC")

        vpc_subnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC)

        # Create a SageMakerDomain for the SageMaker Studio
        domain = sagemaker.CfnDomain(
            self,
            "SageMakerDomain",
            auth_mode="IAM",
            domain_name="SageMakerDomain",
            default_user_settings=user_settings,
            subnet_ids=vpc_subnets.subnet_ids,
            vpc_id=vpc.vpc_id,
        )

        # Create a SageMakerUserProfile for the SageMaker Studio
        profile = {"team": "aws", "name": "dinesh"}
        sagemaker.CfnUserProfile(
            self,
            "SMUserProfile",
            domain_id=domain.attr_domain_id,
            user_profile_name=f"{profile['team']}-{profile['name']}",
            user_settings=user_settings,
        )