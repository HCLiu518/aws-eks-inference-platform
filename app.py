#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_eks_inference.aws_eks_inference_stack import AwsEksInferenceStack


app = cdk.App()
env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')
    )
AwsEksInferenceStack(app, "AwsEksInferenceStack",
    env=env
    )

app.synth()
