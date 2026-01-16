# AWS Deployment Guide

This guide covers multiple approaches to deploy the voice cloning service on Amazon AWS.

## Table of Contents

1. [EC2 Deployment (Recommended for GPU)](#ec2-deployment)
2. [ECS with Fargate (Serverless CPU)](#ecs-fargate-deployment)
3. [ECS with EC2 (GPU Support)](#ecs-ec2-gpu-deployment)
4. [Cost Estimation](#cost-estimation)
5. [Security Best Practices](#security-best-practices)

---

## EC2 Deployment

Best for: GPU-accelerated inference, full control, cost-effective for 24/7 operation

### Prerequisites

- AWS account with billing enabled
- AWS CLI installed and configured (`aws configure`)
- SSH key pair created in AWS console

### Step 1: Launch EC2 Instance

#### For CPU Version

```bash
# Launch Ubuntu instance (t3.xlarge recommended: 4 vCPU, 16GB RAM)
aws ec2 run-instances \
    --image-id ami-0c7217cdde317cfec \
    --instance-type t3.xlarge \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50,"VolumeType":"gp3"}}]' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=voice-cloning-cpu}]'
```

#### For GPU Version

```bash
# Launch GPU instance (g4dn.xlarge: 1 NVIDIA T4 GPU, 4 vCPU, 16GB RAM)
aws ec2 run-instances \
    --image-id ami-0c7217cdde317cfec \
    --instance-type g4dn.xlarge \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=voice-cloning-gpu}]'
```

### Step 2: Configure Security Group

Allow inbound traffic on port 5002 (web interface) and 22 (SSH):

```bash
# Create security group
aws ec2 create-security-group \
    --group-name voice-cloning-sg \
    --description "Security group for voice cloning service" \
    --vpc-id vpc-xxxxxxxxx

# Allow SSH (your IP only - replace X.X.X.X)
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 22 \
    --cidr X.X.X.X/32

# Allow web interface (use ALB/CloudFront for production)
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 5002 \
    --cidr 0.0.0.0/0
```

### Step 3: SSH and Install Dependencies

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@<instance-public-ip>

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# For GPU: Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Log out and back in for docker group to take effect
exit
ssh -i your-key.pem ubuntu@<instance-public-ip>
```

### Step 4: Deploy Application

```bash
# Clone repository
git clone <your-repo-url>
cd speech_generator

# Create directories
mkdir -p voice_samples output

# Build and start service (CPU)
docker-compose build
docker-compose up -d

# OR for GPU
docker-compose --profile gpu build
docker-compose --profile gpu up -d
```

### Step 5: Verify Deployment

```bash
# Check logs
docker-compose logs -f

# Test the service
curl http://localhost:5002

# Access from browser
# http://<instance-public-ip>:5002
```

### Step 6: Enable Auto-Start on Reboot

```bash
# Create systemd service
sudo nano /etc/systemd/system/voice-cloning.service
```

Add this content:

```ini
[Unit]
Description=Voice Cloning Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/speech_generator
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
```

Enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable voice-cloning.service
sudo systemctl start voice-cloning.service
```

---

## ECS Fargate Deployment

Best for: Serverless CPU workloads, automatic scaling, pay-per-use

### Prerequisites

- AWS CLI configured
- Docker image pushed to Amazon ECR

### Step 1: Push Image to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name voice-cloning

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag image
docker build -t voice-cloning .
docker tag voice-cloning:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/voice-cloning:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/voice-cloning:latest
```

### Step 2: Create EFS for Persistent Storage

```bash
# Create EFS file system for model persistence
aws efs create-file-system \
    --performance-mode generalPurpose \
    --throughput-mode bursting \
    --encrypted \
    --tags Key=Name,Value=voice-cloning-models

# Create mount targets (repeat for each subnet)
aws efs create-mount-target \
    --file-system-id fs-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --security-groups sg-xxxxxxxxx
```

### Step 3: Create Task Definition

Create `task-definition.json`:

```json
{
  "family": "voice-cloning",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "4096",
  "memory": "16384",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "voice-cloning",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/voice-cloning:latest",
      "portMappings": [
        {
          "containerPort": 5002,
          "protocol": "tcp"
        }
      ],
      "command": ["python", "web_server.py"],
      "environment": [
        {
          "name": "PYTHONUNBUFFERED",
          "value": "1"
        }
      ],
      "mountPoints": [
        {
          "sourceVolume": "models",
          "containerPath": "/app/models",
          "readOnly": false
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/voice-cloning",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "volumes": [
    {
      "name": "models",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxxxxxx",
        "transitEncryption": "ENABLED",
        "authorizationConfig": {
          "iam": "ENABLED"
        }
      }
    }
  ]
}
```

Register the task definition:

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 4: Create ECS Cluster and Service

```bash
# Create cluster
aws ecs create-cluster --cluster-name voice-cloning-cluster

# Create service with ALB
aws ecs create-service \
    --cluster voice-cloning-cluster \
    --service-name voice-cloning-service \
    --task-definition voice-cloning \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[sg-xxxxxxxxx],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/voice-cloning-tg/xxxxxxxxx,containerName=voice-cloning,containerPort=5002"
```

---

## ECS EC2 GPU Deployment

Best for: GPU acceleration with managed orchestration

### Step 1: Launch GPU-Enabled ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name voice-cloning-gpu-cluster

# Launch EC2 instances with ECS-optimized GPU AMI
aws ec2 run-instances \
    --image-id ami-xxxxxxxxx \
    --instance-type g4dn.xlarge \
    --iam-instance-profile Name=ecsInstanceRole \
    --user-data file://user-data.sh \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx
```

Create `user-data.sh`:

```bash
#!/bin/bash
echo ECS_CLUSTER=voice-cloning-gpu-cluster >> /etc/ecs/ecs.config
echo ECS_ENABLE_GPU_SUPPORT=true >> /etc/ecs/ecs.config
```

### Step 2: Create GPU Task Definition

Modify the previous task definition to include GPU resources:

```json
{
  "requiresCompatibilities": ["EC2"],
  "containerDefinitions": [
    {
      "name": "voice-cloning-gpu",
      "resourceRequirements": [
        {
          "type": "GPU",
          "value": "1"
        }
      ],
      "environment": [
        {
          "name": "NVIDIA_VISIBLE_DEVICES",
          "value": "all"
        }
      ]
    }
  ]
}
```

---

## Cost Estimation

### EC2 Pricing (us-east-1, monthly)

| Instance Type | vCPU | RAM | GPU | Cost/Month (24/7) | Use Case |
|--------------|------|-----|-----|-------------------|----------|
| t3.xlarge | 4 | 16GB | None | ~$121 | CPU inference |
| t3.2xlarge | 8 | 32GB | None | ~$242 | CPU high-volume |
| g4dn.xlarge | 4 | 16GB | T4 (16GB) | ~$391 | GPU inference |
| g4dn.2xlarge | 8 | 32GB | T4 (16GB) | ~$557 | GPU high-volume |

Add: EBS storage (~$8/100GB/month), data transfer costs

### ECS Fargate Pricing

- CPU: $0.04048/vCPU/hour
- Memory: $0.004445/GB/hour
- 4 vCPU, 16GB RAM running 24/7: ~$172/month
- Add: EFS storage ($0.30/GB/month), ALB ($16/month), data transfer

### Recommendations

- **Development/Testing**: t3.xlarge EC2 or Fargate with auto-scaling
- **Production CPU**: Fargate with ALB and auto-scaling
- **Production GPU**: g4dn.xlarge EC2 with reserved instance (40% savings)
- **High Volume**: Multiple g4dn instances with load balancer

---

## Security Best Practices

### 1. Network Security

```bash
# Use VPC with private subnets
# Put ALB in public subnet, ECS tasks in private subnet
# Use NAT Gateway for outbound traffic

# Restrict security group rules
# - SSH: Your IP only
# - HTTP/HTTPS: Through ALB only
# - Internal: Allow ALB -> ECS communication
```

### 2. IAM Roles

Create minimal IAM policies:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "elasticfilesystem:ClientMount",
        "elasticfilesystem:ClientWrite"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Encryption

- Enable EBS encryption for EC2 instances
- Use encrypted EFS file systems
- Enable SSL/TLS with ACM certificate on ALB
- Use AWS Secrets Manager for sensitive configuration

### 4. Monitoring

```bash
# Enable CloudWatch logs
aws logs create-log-group --log-group-name /ecs/voice-cloning

# Set up CloudWatch alarms
aws cloudwatch put-metric-alarm \
    --alarm-name voice-cloning-high-cpu \
    --alarm-description "Alert when CPU exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2
```

### 5. Access Control

- Use Application Load Balancer with AWS WAF
- Implement API authentication (API Gateway + Lambda authorizer)
- Use AWS Cognito for user authentication
- Enable CloudTrail for audit logging

---

## Production Deployment Architecture

### Recommended Setup

```
Internet
    |
CloudFront (CDN) + WAF
    |
Application Load Balancer (SSL/TLS)
    |
    +-- Target Group
         |
         +-- ECS Service (Auto-scaling 1-5 tasks)
              |
              +-- Task 1 (Fargate, 4vCPU, 16GB)
              +-- Task 2 (Fargate, 4vCPU, 16GB)
              +-- ...
              |
              EFS (Shared model storage)
```

### Benefits

- Auto-scaling based on CPU/memory/request count
- Zero-downtime deployments
- DDoS protection via CloudFront + WAF
- SSL/TLS termination at ALB
- Persistent model storage via EFS
- CloudWatch monitoring and logging

---

## Quick Start Commands

### EC2 CPU Deployment

```bash
# 1. Launch instance and SSH in
# 2. Run these commands:
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
git clone <repo-url>
cd speech_generator
docker-compose up -d
```

### EC2 GPU Deployment

```bash
# After SSH into g4dn instance:
curl -fsSL https://get.docker.com | sudo sh
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
git clone <repo-url>
cd speech_generator
docker-compose --profile gpu up -d
```

---

## Troubleshooting

### Issue: Model download fails

```bash
# Check DNS resolution
docker exec voice-generator ping -c 3 coqui.gateway.scarf.sh

# If DNS fails, use fallback script
docker exec voice-generator python download_model_configs.py
```

### Issue: Out of memory

```bash
# Check memory usage
docker stats

# Solution: Upgrade to larger instance or add swap
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue: GPU not detected

```bash
# Verify NVIDIA drivers
nvidia-smi

# Verify Docker can access GPU
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Issue: Port 5002 not accessible

```bash
# Check if service is running
docker ps

# Check if port is listening
sudo netstat -tlnp | grep 5002

# Check security group allows inbound traffic on port 5002
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx
```

---

## Support

For issues specific to:
- AWS infrastructure: AWS Support
- Application code: GitHub Issues
- Docker/Compose: Docker Documentation
