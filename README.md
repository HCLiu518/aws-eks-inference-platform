# Auto-Scaling AI Inference Platform (Amazon EKS)

A production-grade Kubernetes cluster designed for **"Scale-to-Zero"** AI inference. This platform leverages Amazon EKS and the Cluster Autoscaler to provision expensive GPU nodes (`g5.xlarge`) *only* when inference traffic exists, reducing idle compute costs by 100%.

## 🏗 Architecture

This project moves beyond static EC2 deployments by introducing an orchestration layer that separates **System Management** from **AI Workloads**.

* **Control Plane:** Amazon EKS (Kubernetes v1.30)
* **System Node (Always On):** A small, cost-effective `t3.medium` node that runs the Autoscaler, CoreDNS, and Metrics Server.
* **GPU Nodes (Ephemeral):** A "Sleeping Giant" node group of `g5.xlarge` (NVIDIA A10G) instances. These scale from **0 to N** automatically based on Pod demand.
* **Inference Engine:** vLLM serving **Meta-Llama-3.1-8B-Instruct**.

## 🚀 Key Features

* **Zero-to-Scale Architecture:** The GPU Node Group is configured with `min_size=0`. If no AI models are running, no GPU instances exist in the account.
* **Taints & Tolerations:** Implemented `accelerator=gpu:NoSchedule` taints to ensure system pods (like logging agents) never accidentally trigger an expensive GPU node launch.
* **Storage Optimization:** Configured custom Launch Templates with **100GB EBS volumes** to prevent "Disk Pressure" crashes common with large LLM weights (Llama-3 is ~16GB).
* **Infrastructure-as-Code:** Fully defined in Python (AWS CDK), including VPC, IAM Roles, and Security Groups.

## 🛠 Prerequisites

* AWS CLI (v2) & CDK CLI (`npm install -g aws-cdk`)
* Python 3.8+
* `kubectl` (v1.30+)
* Hugging Face Access Token (Read permissions)

## 📦 Deployment Guide

### 1. Initialize Infrastructure
Deploy the VPC and EKS Control Plane using CDK.
```bash
# Create virtual environment
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt

# Deploy the Stack
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION="us-east-2"
cdk deploy
```

### 2. Connect to Cluster
Update your local kubeconfig to authenticate with the cluster.
```bash
aws eks update-kubeconfig --name AICluster --region us-east-2
```

### 3. Install System Components
Apply the NVIDIA Device Plugin (to detect GPUs) and the Cluster Autoscaler.
```bash
# NVIDIA Device Plugin
kubectl apply -f [https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.16.2/deployments/static/nvidia-device-plugin.yml](https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.16.2/deployments/static/nvidia-device-plugin.yml)

# Cluster Autoscaler (Auto-Discovery Mode)
kubectl apply -f cluster-autoscaler-autodiscover.yaml
```
### 4. Deploy Llama-3
Create a Kubernetes Secret for your token and apply the deployment manifest.
```bash
kubectl create secret generic hf-token --from-literal=token=YOUR_HUGGING_FACE_TOKEN
kubectl apply -f llama-deployment.yaml
```

## 📊 Cost Optimization Strategy
| State | Active Resources | Estimated Cost |
| :--- | :--- | :--- |
| **Idle (No Traffic)** | 1x `t3.medium` (System Node) | ~$0.04 / hour |
| **Active (Inference)** | 1x `t3.medium` + 1x `g5.xlarge` | ~$1.05 / hour |

### Mechanism:
1. User requests the Llama-3 Deployment.
2. Kubernetes Scheduler sees `nvidia.com/gpu: 1` requirement.
3. Scheduler fails to find a GPU node (Current count: 0).
4. Pod status changes to `Pending`.
5. Cluster Autoscaler detects `Pending` pod and calls AWS EC2 API to launch a `g5.xlarge`.
6. Once the user deletes the deployment, the GPU node becomes empty and is terminated by AWS after 10 minutes.

## 🧪 Benchmarks
* **Model:** Meta-Llama-3.1-8B-Instruct (FP16, Quantization: None)
* **Throughput:** ~1,900 tokens/sec (Batch Size 64)
* **Latency:** <50ms Inter-Token Latency

## ⚠️ Cleanup
To avoid ongoing EKS Control Plane charges ($0.10/hr), destroy the stack when finished.
```bash
cdk destroy
```
