from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct
from aws_cdk.lambda_layer_kubectl_v30 import KubectlV30Layer

class AwsEksInferenceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create a VPC for the Cluster
        vpc = ec2.Vpc(self, "EksVpc", max_azs=2)

        # 2. IAM Role for the Cluster Admin (YOU)
        # This ensures you can run 'kubectl' commands later
        cluster_admin = iam.Role(self, "ClusterAdmin",
            assumed_by=iam.AccountRootPrincipal()
        )

        # 3. The EKS Cluster (Control Plane)
        cluster = eks.Cluster(self, "AICluster",
            version=eks.KubernetesVersion.V1_30,
            vpc=vpc,
            default_capacity=0,  # We manage nodes explicitly
            masters_role=cluster_admin,
            kubectl_layer=KubectlV30Layer(self, "KubectlLayer")
        )

        # 4. Add a "System" Node Group (CPU)
        # We need at least one small node to run CoreDNS and the Autoscaler
        system_nodes = cluster.add_nodegroup_capacity("SystemNodes",
            instance_types=[ec2.InstanceType("t3.medium")],
            min_size=1,
            max_size=2,
            ami_type=eks.NodegroupAmiType.AL2_X86_64
        )

        # 5. GPU Node (The Sleeping Giant - g5.xlarge)
        # min_size=0 means it costs $0 until we need it.
        gpu_nodes = cluster.add_nodegroup_capacity("GpuNodes",
            instance_types=[ec2.InstanceType("g5.xlarge")],
            min_size=0,
            max_size=3, # Cap risk at 3 GPUs
            ami_type=eks.NodegroupAmiType.AL2_X86_64_GPU,
            disk_size=100,
            # Taints: Prevent random pods from stealing expensive GPU slots
            taints=[eks.TaintSpec(
                effect=eks.TaintEffect.NO_SCHEDULE,
                key="accelerator",
                value="gpu"
            )],
            # Labels: Help us target this node later
            labels={"accelerator": "gpu"}
        )

        # 6. Grant Permissions (Crucial for Scaling)
        # The System Node needs permission to scale the ASG up/down
        autoscaler_policy = iam.PolicyStatement(
            actions=[
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeAutoScalingInstances",
                "autoscaling:DescribeLaunchConfigurations",
                "autoscaling:DescribeTags",
                "autoscaling:SetDesiredCapacity",
                "autoscaling:TerminateInstanceInAutoScalingGroup",
                "ec2:DescribeLaunchTemplateVersions"
            ],
            resources=["*"]
        )
        system_nodes.role.add_to_principal_policy(autoscaler_policy)

        # 7. Output the Config Command
        CfnOutput(self, "ConfigCommand",
            value=f"aws eks update-kubeconfig --name {cluster.cluster_name} --region {self.region}"
        )