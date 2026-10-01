import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from study.models import StudyCertification, Topic, Lab


def make_aws_vpc_svg(title: str, subnets_info: list) -> str:
    """Generates an AWS Multi-AZ VPC Architecture SVG diagram."""
    subnet_rows = "".join(
        f'<text x="250" y="{260 + i * 16}" text-anchor="middle" fill="#94a3b8" font-family="monospace" font-size="10">{s}</text>'
        for i, s in enumerate(subnets_info)
    )
    return f"""<svg viewBox="0 0 540 320" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
  <defs>
    <linearGradient id="awsBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0b1120"/>
      <stop offset="100%" stop-color="#020617"/>
    </linearGradient>
    <linearGradient id="vpcGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#awsBg)" rx="12"/>
  <text x="270" y="28" text-anchor="middle" fill="#f8fafc" font-family="sans-serif" font-size="13" font-weight="bold">{title}</text>
  
  <!-- Outer Cloud Boundary -->
  <rect x="20" y="42" width="500" height="200" rx="10" fill="none" stroke="#ff9900" stroke-width="1.5" stroke-dasharray="4,4"/>
  <text x="32" y="58" fill="#ff9900" font-family="sans-serif" font-size="10" font-weight="bold">AWS Cloud (Region: us-east-1)</text>

  <!-- VPC Boundary -->
  <rect x="35" y="66" width="470" height="166" rx="8" fill="url(#vpcGrad)" stroke="#38bdf8" stroke-width="1.2"/>
  <text x="45" y="80" fill="#38bdf8" font-family="sans-serif" font-size="10" font-weight="bold">VPC 10.0.0.0/16</text>

  <!-- Availability Zone A -->
  <rect x="50" y="90" width="210" height="132" rx="6" fill="#1e1b4b" stroke="#818cf8" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="60" y="105" fill="#a5b4fc" font-family="sans-serif" font-size="9" font-weight="bold">AZ us-east-1a</text>
  
  <!-- AZ-A Public Subnet -->
  <rect x="60" y="112" width="190" height="46" rx="4" fill="#0f172a" stroke="#22c55e" stroke-width="1"/>
  <text x="70" y="125" fill="#4ade80" font-family="sans-serif" font-size="9">Public Subnet 10.0.1.0/24</text>
  <rect x="180" y="128" width="60" height="22" rx="3" fill="#14532d"/>
  <text x="210" y="142" text-anchor="middle" fill="#bbf7d0" font-family="monospace" font-size="8">ALB Node A</text>

  <!-- AZ-A Private Subnet -->
  <rect x="60" y="165" width="190" height="50" rx="4" fill="#0f172a" stroke="#3b82f6" stroke-width="1"/>
  <text x="70" y="178" fill="#60a5fa" font-family="sans-serif" font-size="9">Private App 10.0.11.0/24</text>
  <rect x="160" y="181" width="80" height="26" rx="3" fill="#1e3a8a"/>
  <text x="200" y="197" text-anchor="middle" fill="#bfdbfe" font-family="monospace" font-size="8">EC2 (ASG Node)</text>

  <!-- Availability Zone B -->
  <rect x="280" y="90" width="210" height="132" rx="6" fill="#1e1b4b" stroke="#818cf8" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="290" y="105" fill="#a5b4fc" font-family="sans-serif" font-size="9" font-weight="bold">AZ us-east-1b</text>

  <!-- AZ-B Public Subnet -->
  <rect x="290" y="112" width="190" height="46" rx="4" fill="#0f172a" stroke="#22c55e" stroke-width="1"/>
  <text x="300" y="125" fill="#4ade80" font-family="sans-serif" font-size="9">Public Subnet 10.0.2.0/24</text>
  <rect x="410" y="128" width="60" height="22" rx="3" fill="#14532d"/>
  <text x="440" y="142" text-anchor="middle" fill="#bbf7d0" font-family="monospace" font-size="8">ALB Node B</text>

  <!-- AZ-B Private Subnet -->
  <rect x="290" y="165" width="190" height="50" rx="4" fill="#0f172a" stroke="#3b82f6" stroke-width="1"/>
  <text x="300" y="178" fill="#60a5fa" font-family="sans-serif" font-size="9">Private App 10.0.12.0/24</text>
  <rect x="390" y="181" width="80" height="26" rx="3" fill="#1e3a8a"/>
  <text x="430" y="197" text-anchor="middle" fill="#bfdbfe" font-family="monospace" font-size="8">EC2 (ASG Node)</text>

  <!-- Subnet Table Footnote -->
  {subnet_rows}
</svg>"""


def make_aws_serverless_svg(title: str) -> str:
    """Generates an AWS Serverless Microservice SVG diagram."""
    return f"""<svg viewBox="0 0 540 280" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
  <rect width="100%" height="100%" fill="#090d16" rx="12"/>
  <text x="270" y="28" text-anchor="middle" fill="#f8fafc" font-family="sans-serif" font-size="13" font-weight="bold">{title}</text>
  
  <!-- Flow Arrows -->
  <line x1="85" y1="130" x2="140" y2="130" stroke="#f59e0b" stroke-width="3" marker-end="url(#arrow)"/>
  <line x1="230" y1="130" x2="285" y2="130" stroke="#f59e0b" stroke-width="3"/>
  <line x1="375" y1="130" x2="430" y2="130" stroke="#f59e0b" stroke-width="3"/>

  <!-- Client -->
  <rect x="20" y="100" width="70" height="60" rx="6" fill="#1e293b" stroke="#64748b" stroke-width="1.5"/>
  <text x="55" y="128" text-anchor="middle" fill="#e2e8f0" font-family="sans-serif" font-size="10" font-weight="bold">Client</text>
  <text x="55" y="142" text-anchor="middle" fill="#94a3b8" font-family="monospace" font-size="8">curl/Web</text>

  <!-- API Gateway -->
  <rect x="140" y="95" width="90" height="70" rx="8" fill="#701a75" stroke="#d946ef" stroke-width="2"/>
  <text x="185" y="125" text-anchor="middle" fill="#fdf4ff" font-family="sans-serif" font-size="10" font-weight="bold">API Gateway</text>
  <text x="185" y="142" text-anchor="middle" fill="#f5d0fe" font-family="monospace" font-size="8">HTTP API</text>
  <text x="185" y="154" text-anchor="middle" fill="#e879f9" font-family="monospace" font-size="8">POST /orders</text>

  <!-- Lambda -->
  <rect x="285" y="95" width="90" height="70" rx="8" fill="#7c2d12" stroke="#ea580c" stroke-width="2"/>
  <text x="330" y="125" text-anchor="middle" fill="#fff7ed" font-family="sans-serif" font-size="10" font-weight="bold">AWS Lambda</text>
  <text x="330" y="142" text-anchor="middle" fill="#fed7aa" font-family="monospace" font-size="8">Python 3.12</text>
  <text x="330" y="154" text-anchor="middle" fill="#fb923c" font-family="monospace" font-size="8">ProcessOrder</text>

  <!-- DynamoDB -->
  <rect x="430" y="95" width="90" height="70" rx="8" fill="#14532d" stroke="#22c55e" stroke-width="2"/>
  <text x="475" y="125" text-anchor="middle" fill="#f0fdf4" font-family="sans-serif" font-size="10" font-weight="bold">DynamoDB</text>
  <text x="475" y="142" text-anchor="middle" fill="#bbf7d0" font-family="monospace" font-size="8">OrdersTable</text>
  <text x="475" y="154" text-anchor="middle" fill="#86efac" font-family="monospace" font-size="8">PK: order_id</text>

  <!-- Legend -->
  <text x="270" y="215" text-anchor="middle" fill="#cbd5e1" font-family="sans-serif" font-size="10">Event-driven, serverless execution: zero idle compute cost, auto-scaling up to thousands of RPS.</text>
  <text x="270" y="235" text-anchor="middle" fill="#64748b" font-family="monospace" font-size="9">IAM Role: AWSLambdaBasicExecutionRole + AmazonDynamoDBFullAccess (Scoped)</text>
</svg>"""


def make_aws_edge_svg(title: str) -> str:
    """Generates an AWS CloudFront + S3 OAC Edge Delivery SVG diagram."""
    return f"""<svg viewBox="0 0 540 280" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
  <rect width="100%" height="100%" fill="#090d16" rx="12"/>
  <text x="270" y="28" text-anchor="middle" fill="#f8fafc" font-family="sans-serif" font-size="13" font-weight="bold">{title}</text>

  <!-- Connectors -->
  <line x1="90" y1="130" x2="160" y2="130" stroke="#3b82f6" stroke-width="3"/>
  <line x1="260" y1="130" x2="330" y2="130" stroke="#22c55e" stroke-width="3"/>
  <line x1="430" y1="130" x2="460" y2="130" stroke="#22c55e" stroke-width="3"/>

  <!-- Users -->
  <rect x="20" y="100" width="70" height="60" rx="6" fill="#1e293b" stroke="#64748b" stroke-width="1.5"/>
  <text x="55" y="128" text-anchor="middle" fill="#e2e8f0" font-family="sans-serif" font-size="10" font-weight="bold">Global Users</text>
  <text x="55" y="142" text-anchor="middle" fill="#94a3b8" font-family="monospace" font-size="8">HTTPS / TLS</text>

  <!-- CloudFront Distribution -->
  <rect x="160" y="95" width="100" height="70" rx="8" fill="#1e1b4b" stroke="#6366f1" stroke-width="2"/>
  <text x="210" y="125" text-anchor="middle" fill="#e0e7ff" font-family="sans-serif" font-size="10" font-weight="bold">CloudFront CDN</text>
  <text x="210" y="142" text-anchor="middle" fill="#c7d2fe" font-family="monospace" font-size="8">Edge Cache</text>
  <text x="210" y="154" text-anchor="middle" fill="#a5b4fc" font-family="monospace" font-size="8">OAC Signing</text>

  <!-- OAC Badge -->
  <rect x="280" y="118" width="50" height="24" rx="4" fill="#065f46" stroke="#10b981" stroke-width="1"/>
  <text x="305" y="134" text-anchor="middle" fill="#a7f3d0" font-family="monospace" font-size="8" font-weight="bold">OAC</text>

  <!-- Private S3 Bucket -->
  <rect x="350" y="95" width="140" height="70" rx="8" fill="#0c4a6e" stroke="#0284c7" stroke-width="2"/>
  <text x="420" y="125" text-anchor="middle" fill="#f0f9ff" font-family="sans-serif" font-size="10" font-weight="bold">Private S3 Bucket</text>
  <text x="420" y="142" text-anchor="middle" fill="#bae6fd" font-family="monospace" font-size="8">Block Public Access: ON</text>
  <text x="420" y="154" text-anchor="middle" fill="#7dd3fc" font-family="monospace" font-size="8">Policy: SourceArn == CFN</text>

  <text x="270" y="215" text-anchor="middle" fill="#cbd5e1" font-family="sans-serif" font-size="10">Direct S3 access returns 403 Forbidden. Content is delivered exclusively through CloudFront Edge locations.</text>
  <text x="270" y="235" text-anchor="middle" fill="#64748b" font-family="monospace" font-size="9">Free Tier: 1 TB CloudFront data transfer out + 10,000,000 HTTP/HTTPS requests/month.</text>
</svg>"""


class Command(BaseCommand):
    help = "Seeds 8 production-grade AWS Solutions Architect Associate (SAA-C03) architecture labs"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding comprehensive AWS SAA-C03 architecture labs..."))

        aws_cert = StudyCertification.objects.filter(code="AWS-SAA-C03").first()
        if not aws_cert:
            self.stdout.write(self.style.ERROR("AWS-SAA-C03 certification not found. Please run seed_study_topics first."))
            return

        labs_data = [
            # 1. Resilient: Multi-AZ Web Tier with ALB and Auto Scaling
            {
                "topic_ref": "2.1",
                "title": "Highly Available Multi-AZ Web Tier with ALB and Auto Scaling",
                "slug": "lab-aws-multi-az-alb-asg",
                "difficulty": "intermediate",
                "estimated_time_minutes": 45,
                "estimated_cost_usd": Decimal("0.08"),
                "free_tier_eligible": False,  # ALB has minimal hourly charge outside 750h/mo shared
                "prerequisites": "AWS Account, IAM permissions for EC2, Auto Scaling, ELB, and VPC.",
                "objectives": [
                    "Design and launch an Application Load Balancer across 2 public Availability Zones.",
                    "Configure an Auto Scaling Group in private subnets with a minimum of 2 and maximum of 4 EC2 instances.",
                    "Implement Target Group HTTP health checks to automatically replace failing instances.",
                    "Verify cross-zone load balancing and zero-downtime instance replacement."
                ],
                "topology_type": "svg",
                "topology_data": make_aws_vpc_svg("Highly Available Multi-AZ Web Tier (ALB + ASG)", [
                    "Public Subnet 1: 10.0.1.0/24 (AZ us-east-1a) - ALB Node A",
                    "Public Subnet 2: 10.0.2.0/24 (AZ us-east-1b) - ALB Node B",
                    "Private Subnet 1: 10.0.11.0/24 (AZ us-east-1a) - ASG EC2 Instances",
                    "Private Subnet 2: 10.0.12.0/24 (AZ us-east-1b) - ASG EC2 Instances"
                ]),
                "addressing_table": [
                    {"device": "VPC", "interface": "CIDR Block", "ip": "10.0.0.0", "subnet": "255.255.0.0 (/16)", "vlan": "us-east-1", "default_gateway": "N/A"},
                    {"device": "Public Subnet 1", "interface": "us-east-1a", "ip": "10.0.1.0", "subnet": "255.255.255.0 (/24)", "vlan": "Public", "default_gateway": "Internet Gateway"},
                    {"device": "Public Subnet 2", "interface": "us-east-1b", "ip": "10.0.2.0", "subnet": "255.255.255.0 (/24)", "vlan": "Public", "default_gateway": "Internet Gateway"},
                    {"device": "Private Subnet 1", "interface": "us-east-1a", "ip": "10.0.11.0", "subnet": "255.255.255.0 (/24)", "vlan": "Private App", "default_gateway": "NAT Gateway"},
                    {"device": "Private Subnet 2", "interface": "us-east-1b", "ip": "10.0.12.0", "subnet": "255.255.255.0 (/24)", "vlan": "Private App", "default_gateway": "NAT Gateway"},
                ],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Create Security Groups for ALB and App Instances",
                        "instructions": "Navigate to EC2 > Security Groups > Create security group. Create 'alb-sg' allowing Inbound HTTP (port 80) from 0.0.0.0/0. Create 'app-sg' allowing Inbound HTTP (port 80) restricted to source Security Group 'alb-sg' (Security Group chaining).",
                        "verify_prompt": "Confirm 'app-sg' does NOT allow direct traffic from 0.0.0.0/0."
                    },
                    {
                        "step_num": 2,
                        "title": "Create EC2 Launch Template with User Data Script",
                        "instructions": "Go to EC2 > Launch Templates > Create launch template. Name it 'web-template'. Select Amazon Linux 2023, t2.micro (Free Tier eligible), assign 'app-sg'. In Advanced Details > User Data, paste the script that installs Apache HTTP and writes the instance AZ to index.html.",
                        "verify_prompt": "Ensure Launch Template version is Default and security group is attached."
                    },
                    {
                        "step_num": 3,
                        "title": "Create Target Group & Application Load Balancer",
                        "instructions": "Go to EC2 > Target Groups > Create target group (Instances, HTTP:80). Then go to Load Balancers > Create Application Load Balancer ('web-alb'). Select your VPC and check both us-east-1a and us-east-1b Public Subnets. Add Listener HTTP:80 forwarding to the Target Group.",
                        "verify_prompt": "Wait for ALB state to become 'Active' and copy the DNS Name."
                    },
                    {
                        "step_num": 4,
                        "title": "Configure Auto Scaling Group across Private Subnets",
                        "instructions": "Go to EC2 > Auto Scaling Groups > Create Auto Scaling group ('web-asg'). Select 'web-template'. In Network, select Private Subnet 1 and Private Subnet 2. Under Load balancing, attach to existing target group. Set Group size: Desired 2, Min 2, Max 4.",
                        "verify_prompt": "Check Target Group targets: verify 2 instances register and transition to 'healthy'."
                    }
                ],
                "hints": [
                    "Exam Tip: Security Group chaining (setting the source of app-sg to alb-sg) guarantees that traffic cannot bypass the load balancer.",
                    "Gotcha: Application Load Balancers require at least TWO Availability Zones to ensure high availability. Selecting only one will fail validation."
                ],
                "setup_template_type": "cloudformation",
                "setup_template": """AWSTemplateFormatVersion: '2010-09-09'
Description: 'AWS SAA-C03: Highly Available Multi-AZ ALB and Auto Scaling Architecture'

Parameters:
  VpcCIDR:
    Type: String
    Default: 10.0.0.0/16
  LatestAmiId:
    Type: 'AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>'
    Default: '/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64'

Resources:
  LabVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCIDR
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: Lab-MultiAZ-VPC

  InternetGateway:
    Type: AWS::EC2::InternetGateway
  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref LabVPC
      InternetGatewayId: !Ref InternetGateway

  PubSubnetA:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref LabVPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true
  PubSubnetB:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref LabVPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true

  PubRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref LabVPC
  PubRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref PubRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway
  AssocPubA:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PubSubnetA
      RouteTableId: !Ref PubRouteTable
  AssocPubB:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PubSubnetB
      RouteTableId: !Ref PubRouteTable

  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Allow inbound HTTP from Internet
      VpcId: !Ref LabVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0

  AppSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Allow HTTP only from ALB Security Group
      VpcId: !Ref LabVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          SourceSecurityGroupId: !Ref ALBSecurityGroup

  TargetGroup:
    Type: AWS::EC2::TargetGroup
    Properties:
      Name: web-target-group
      Port: 80
      Protocol: HTTP
      VpcId: !Ref LabVPC
      HealthCheckPath: /
      HealthCheckIntervalSeconds: 15
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 2

  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: web-alb
      Scheme: internet-facing
      SecurityGroups: [!Ref ALBSecurityGroup]
      Subnets: [!Ref PubSubnetA, !Ref PubSubnetB]

  ALBListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 80
      Protocol: HTTP
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup

  LaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateData:
        ImageId: !Ref LatestAmiId
        InstanceType: t2.micro
        SecurityGroupIds: [!Ref AppSecurityGroup]
        UserData:
          Fn::Base64: !Sub |
            #!/bin/bash
            yum install -y httpd
            systemctl start httpd
            systemctl enable httpd
            TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
            AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone)
            IID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
            echo "<h1>AWS SAA-C03 HA Web Tier</h1><p>Zone: <b>$AZ</b> | Instance: <b>$IID</b></p>" > /var/www/html/index.html

  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      AutoScalingGroupName: web-asg
      LaunchTemplate:
        LaunchTemplateId: !Ref LaunchTemplate
        Version: !GetAtt LaunchTemplate.LatestVersionNumber
      MinSize: '2'
      MaxSize: '4'
      DesiredCapacity: '2'
      VPCZoneIdentifier: [!Ref PubSubnetA, !Ref PubSubnetB]
      TargetGroupARNs: [!Ref TargetGroup]
      HealthCheckType: ELB
      HealthCheckGracePeriod: 120

Outputs:
  AlbDnsName:
    Description: Application Load Balancer DNS Name
    Value: !GetAtt ApplicationLoadBalancer.DNSName
""",
                "solution": """# Terraform Architecture Solution for Highly Available ALB + ASG
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

# 1. VPC & Subnets
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "terraform-ha-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# 2. Security Groups
resource "aws_security_group" "alb_sg" {
  name        = "tf-alb-sg"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "app_sg" {
  name   = "tf-app-sg"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 3. ALB & Target Group
resource "aws_lb_target_group" "tg" {
  name     = "tf-web-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  health_check {
    path                = "/"
    interval            = 15
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb" "alb" {
  name               = "tf-web-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg.arn
  }
}

# 4. Launch Template & ASG
resource "aws_launch_template" "lt" {
  name_prefix   = "tf-web-"
  image_id      = "ami-0c101f26f147fa7fd" # Amazon Linux 2023 in us-east-1
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  user_data = base64encode(<<-EOF
              #!/bin/bash
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Deployed via Terraform</h1>" > /var/www/html/index.html
              EOF
  )
}

resource "aws_autoscaling_group" "asg" {
  name                = "tf-web-asg"
  desired_capacity    = 2
  max_size            = 4
  min_size            = 2
  target_group_arns   = [aws_lb_target_group.tg.arn]
  vpc_zone_identifier = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  launch_template {
    id      = aws_launch_template.lt.id
    version = "$Latest"
  }
}

output "alb_dns_name" {
  value = aws_lb.alb.dns_name
}
""",
                "aws_verification_checks": [
                    {
                        "service": "elbv2",
                        "check_type": "Verify ALB HTTP 200 Response",
                        "verify_prompt": "Send HTTP curl request to the ALB DNS name: curl -I http://<ALB-DNS-NAME>. Verify HTTP/1.1 200 OK.",
                        "expected": "HTTP/1.1 200 OK"
                    },
                    {
                        "service": "elbv2",
                        "check_type": "Verify Multi-AZ Target Health",
                        "verify_prompt": "Check AWS Management Console > Target Groups > Target health. Confirm at least 2 instances in distinct AZs report status 'healthy'.",
                        "expected": "healthy"
                    },
                    {
                        "service": "autoscaling",
                        "check_type": "Simulate Failure & Zero-Downtime Auto-Recovery",
                        "verify_prompt": "Terminate one of the EC2 instances in the AWS console. Verify that the ALB continues serving traffic from the healthy instance and Auto Scaling automatically spins up a replacement instance within 180 seconds.",
                        "expected": "Auto-recovery successful"
                    }
                ],
                "teardown_instructions": """CRITICAL: Perform teardown in this exact order to avoid lingering charges:
1. Go to EC2 > Auto Scaling Groups > Select 'web-asg' > Delete. (This terminates all running EC2 instances immediately).
2. Go to EC2 > Load Balancers > Select 'web-alb' > Delete.
3. Go to EC2 > Target Groups > Select 'web-target-group' > Delete.
4. Go to EC2 > Launch Templates > Select 'web-template' > Actions > Delete template.
5. If you created a standalone VPC, delete the NAT Gateway, release any allocated Elastic IPs, and delete the VPC.
6. Check your AWS Billing Dashboard / Cost Explorer tomorrow to confirm $0 ongoing cost.""",
            },

            # 2. Secure: Multi-Tier VPC Segmentation with Security Groups & NAT Gateway
            {
                "topic_ref": "1.2",
                "title": "Multi-Tier VPC Segmentation with Private Subnets, NAT Gateway & Security Groups",
                "slug": "lab-aws-vpc-segmentation-nat",
                "difficulty": "intermediate",
                "estimated_time_minutes": 45,
                "estimated_cost_usd": Decimal("0.09"),
                "free_tier_eligible": False,  # NAT Gateway is ~$0.045/hour
                "prerequisites": "AWS Account with VPC and EC2 creation privileges.",
                "objectives": [
                    "Construct a 3-tier VPC architecture with Public Web, Private Application, and Isolated Database subnets.",
                    "Deploy an Elastic IP and NAT Gateway in the Public Subnet to grant outbound-only internet access to private instances.",
                    "Implement defense-in-depth security group chaining: Web SG -> App SG -> DB SG (PostgreSQL 5432).",
                    "Verify Network ACLs vs Security Groups stateful inspection behavior."
                ],
                "topology_type": "svg",
                "topology_data": make_aws_vpc_svg("Multi-Tier VPC Network Segmentation", [
                    "Public Subnet: 10.0.1.0/24 (IGW + NAT Gateway)",
                    "Private App Subnet: 10.0.10.0/24 (Routes to NAT Gateway)",
                    "Isolated DB Subnet: 10.0.20.0/24 (No Internet Route)"
                ]),
                "addressing_table": [
                    {"device": "VPC", "interface": "10.0.0.0/16", "ip": "10.0.0.0", "subnet": "255.255.0.0", "vlan": "Multi-Tier VPC", "default_gateway": "N/A"},
                    {"device": "Public Web Subnet", "interface": "us-east-1a", "ip": "10.0.1.0", "subnet": "255.255.255.0 (/24)", "vlan": "Public Tier", "default_gateway": "IGW"},
                    {"device": "Private App Subnet", "interface": "us-east-1a", "ip": "10.0.10.0", "subnet": "255.255.255.0 (/24)", "vlan": "Private App", "default_gateway": "NAT Gateway"},
                    {"device": "Isolated DB Subnet", "interface": "us-east-1a", "ip": "10.0.20.0", "subnet": "255.255.255.0 (/24)", "vlan": "Isolated DB", "default_gateway": "None (Local Only)"},
                ],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Create 3-Tier Subnets in VPC",
                        "instructions": "Navigate to VPC > Subnets > Create subnet. Create Public Subnet (10.0.1.0/24), Private App Subnet (10.0.10.0/24), and Isolated DB Subnet (10.0.20.0/24).",
                        "verify_prompt": "Confirm all 3 subnets reside inside VPC 10.0.0.0/16."
                    },
                    {
                        "step_num": 2,
                        "title": "Deploy Internet Gateway & NAT Gateway",
                        "instructions": "Create an Internet Gateway and attach to your VPC. Allocate an Elastic IP. Create a NAT Gateway in the Public Subnet (10.0.1.0/24) using that Elastic IP.",
                        "verify_prompt": "Wait for NAT Gateway status to show 'Available'."
                    },
                    {
                        "step_num": 3,
                        "title": "Configure Route Tables",
                        "instructions": "Create Public Route Table: route 0.0.0.0/0 -> Internet Gateway (associate with Public Subnet). Create Private Route Table: route 0.0.0.0/0 -> NAT Gateway (associate with Private App Subnet). Leave DB Subnet on local-only route.",
                        "verify_prompt": "Verify DB Subnet has NO route to 0.0.0.0/0."
                    },
                    {
                        "step_num": 4,
                        "title": "Chain Security Groups (Web -> App -> DB)",
                        "instructions": "Create DB Security Group. Add Inbound Rule: PostgreSQL (port 5432), Source = App Security Group ID (NOT an IP range).",
                        "verify_prompt": "Confirm DB SG references the security group ID as the source."
                    }
                ],
                "hints": [
                    "Exam Tip: Security groups are stateful (inbound allowed traffic is automatically allowed outbound regardless of outbound rules). Network ACLs are stateless.",
                    "Cost Saver: NAT Gateways charge per hour plus data processing fee. Always delete the NAT Gateway and release the EIP when finished!"
                ],
                "setup_template_type": "cloudformation",
                "setup_template": """AWSTemplateFormatVersion: '2010-09-09'
Description: 'AWS SAA-C03: 3-Tier Segmented VPC with NAT Gateway and Chained Security Groups'
Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      Tags: [{Key: Name, Value: SAA-3Tier-VPC}]

  IGW:
    Type: AWS::EC2::InternetGateway
  AttachIGW:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref IGW

  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true

  PrivateAppSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.10.0/24
      AvailabilityZone: !Select [0, !GetAZs '']

  IsolatedDBSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.20.0/24
      AvailabilityZone: !Select [0, !GetAZs '']

  NatEIP:
    Type: AWS::EC2::EIP
    Properties:
      Domain: vpc

  NatGateway:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NatEIP.AllocationId
      SubnetId: !Ref PublicSubnet

  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
  PubDefaultRoute:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref IGW
  AssocPublic:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet
      RouteTableId: !Ref PublicRouteTable

  PrivateRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
  PrivDefaultRoute:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NatGateway
  AssocPrivate:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PrivateAppSubnet
      RouteTableId: !Ref PrivateRouteTable

  WebSG:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Web Tier SG
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

  AppSG:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: App Tier SG
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 8080
          ToPort: 8080
          SourceSecurityGroupId: !Ref WebSG

  DBSG:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: DB Tier SG
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: !Ref AppSG
""",
                "solution": """# Terraform 3-Tier VPC Architecture
resource "aws_vpc" "vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "tf-3tier-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "app" {
  vpc_id            = aws_vpc.vpc.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "db" {
  vpc_id            = aws_vpc.vpc.id
  cidr_block        = "10.0.20.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_eip" "nat" {
  domain = "vpc"
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.vpc.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }
}

resource "aws_route_table_association" "pub" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "priv" {
  subnet_id      = aws_subnet.app.id
  route_table_id = aws_route_table.private.id
}

# Chained Security Groups
resource "aws_security_group" "web_sg" {
  name   = "tf-web-sg"
  vpc_id = aws_vpc.vpc.id
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "app_sg" {
  name   = "tf-app-sg"
  vpc_id = aws_vpc.vpc.id
  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.web_sg.id]
  }
}

resource "aws_security_group" "db_sg" {
  name   = "tf-db-sg"
  vpc_id = aws_vpc.vpc.id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }
}
""",
                "aws_verification_checks": [
                    {
                        "service": "ec2",
                        "check_type": "Verify Private Instance Outbound Internet via NAT Gateway",
                        "verify_prompt": "From an EC2 instance launched in the Private App Subnet (10.0.10.0/24), run: curl -I https://aws.amazon.com. Confirm successful HTTP response while having NO public IP.",
                        "expected": "HTTP 200 via NAT Gateway"
                    },
                    {
                        "service": "ec2",
                        "check_type": "Verify DB Security Group Ingress Isolation",
                        "verify_prompt": "Verify DB Security Group rejects all incoming traffic except traffic with source Security Group ID matching App SG.",
                        "expected": "Chained Ingress Rule Verified"
                    }
                ],
                "teardown_instructions": """CRITICAL TEARDOWN ORDER (Prevent unwanted charges):
1. Delete the NAT Gateway in the VPC console (wait until state shows 'Deleted').
2. Release the Elastic IP (EIP) allocated for the NAT Gateway (unallocated EIPs incur an hourly charge!).
3. Terminate any test EC2 instances.
4. Delete the VPC (subnets, route tables, and internet gateway attachments will be cleaned up).""",
            },

            # 3. High-Performing Serverless: API Gateway + Lambda + DynamoDB
            {
                "topic_ref": "3.5",
                "title": "Serverless Microservice with API Gateway, Python Lambda & DynamoDB",
                "slug": "lab-aws-serverless-api-lambda-dynamodb",
                "difficulty": "beginner",
                "estimated_time_minutes": 35,
                "estimated_cost_usd": Decimal("0.00"),
                "free_tier_eligible": True,  # 100% Free Tier (Lambda 1M free, DynamoDB 25GB free)
                "prerequisites": "AWS Account, IAM permissions for Lambda, API Gateway, and DynamoDB.",
                "objectives": [
                    "Create an Amazon DynamoDB table with on-demand capacity and partition key 'order_id'.",
                    "Author an AWS Lambda function in Python 3.12 that parses JSON payloads and writes items to DynamoDB.",
                    "Expose the Lambda function via Amazon API Gateway HTTP API with route POST /orders.",
                    "Test end-to-end API invocations using curl and inspect persisted DynamoDB items."
                ],
                "topology_type": "svg",
                "topology_data": make_aws_serverless_svg("Serverless Order Processing REST Microservice"),
                "addressing_table": [
                    {"device": "API Gateway", "interface": "HTTP API", "ip": "https://<api-id>.execute-api.us-east-1.amazonaws.com", "subnet": "Serverless Endpoint", "vlan": "Public REST", "default_gateway": "N/A"},
                    {"device": "AWS Lambda", "interface": "Runtime", "ip": "Python 3.12 (ARM64 / Graviton)", "subnet": "AWS Managed Serverless", "vlan": "Microservice", "default_gateway": "N/A"},
                    {"device": "DynamoDB", "interface": "OrdersTable", "ip": "NoSQL Service Endpoint", "subnet": "Global On-Demand", "vlan": "Storage", "default_gateway": "N/A"},
                ],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Create DynamoDB Table",
                        "instructions": "Navigate to DynamoDB > Tables > Create table. Name: 'OrdersTable'. Partition key: 'order_id' (String). Capacity mode: 'On-demand' (Pay per request).",
                        "verify_prompt": "Confirm table status is 'Active' with On-demand capacity."
                    },
                    {
                        "step_num": 2,
                        "title": "Create IAM Execution Role for Lambda",
                        "instructions": "Go to IAM > Roles > Create role. Select AWS Service > Lambda. Attach 'AWSLambdaBasicExecutionRole'. Create an inline policy allowing dynamodb:PutItem and dynamodb:GetItem on 'OrdersTable'.",
                        "verify_prompt": "Ensure policy resource ARN is scoped specifically to OrdersTable."
                    },
                    {
                        "step_num": 3,
                        "title": "Deploy Python Lambda Function",
                        "instructions": "Go to Lambda > Create function. Name: 'CreateOrderFunction'. Runtime: Python 3.12. Attach your created IAM role. In code editor, write the handler that accepts event['body'], generates a UUID order_id, and calls table.put_item(). Click Deploy.",
                        "verify_prompt": "Run a test event in the Lambda console and verify 200 OK returned."
                    },
                    {
                        "step_num": 4,
                        "title": "Create API Gateway HTTP API Integration",
                        "instructions": "Go to API Gateway > Create API > HTTP API. Build integration with 'CreateOrderFunction'. Add route: POST /orders. Deploy to $default stage.",
                        "verify_prompt": "Copy the Invoke URL from the API Gateway stages view."
                    }
                ],
                "hints": [
                    "Exam Tip: API Gateway HTTP APIs are up to 71% cheaper and offer lower latency than traditional REST APIs when API Keys or request validation aren't needed.",
                    "Best Practice: Use On-demand DynamoDB capacity for unpredictable workloads, and switch to Provisioned with auto-scaling for predictable baselines."
                ],
                "setup_template_type": "cloudformation",
                "setup_template": """AWSTemplateFormatVersion: '2010-09-09'
Description: 'AWS SAA-C03: Serverless API Gateway + Lambda + DynamoDB Architecture'
Resources:
  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: OrdersTable
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: order_id
          AttributeType: S
      KeySchema:
        - AttributeName: order_id
          KeyType: HASH

  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal: {Service: lambda.amazonaws.com}
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: DynamoDBOrderAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - dynamodb:PutItem
                  - dynamodb:GetItem
                Resource: !GetAtt OrdersTable.Arn

  OrderFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: CreateOrderFunction
      Runtime: python3.12
      Handler: index.lambda_handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Code:
        ZipFile: |
          import json, uuid, boto3, os
          dynamodb = boto3.resource('dynamodb')
          table = dynamodb.Table('OrdersTable')
          def lambda_handler(event, context):
              try:
                  body = json.loads(event.get('body', '{}'))
                  order_id = str(uuid.uuid4())
                  item = {
                      'order_id': order_id,
                      'customer': body.get('customer', 'Guest'),
                      'item': body.get('item', 'Standard Item'),
                      'amount': str(body.get('amount', '0.00'))
                  }
                  table.put_item(Item=item)
                  return {
                      'statusCode': 201,
                      'headers': {'Content-Type': 'application/json'},
                      'body': json.dumps({'message': 'Order created', 'order_id': order_id})
                  }
              except Exception as e:
                  return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

  HttpApi:
    Type: AWS::ApiGatewayV2::Api
    Properties:
      Name: OrdersHttpApi
      ProtocolType: HTTP

  ApiIntegration:
    Type: AWS::ApiGatewayV2::Integration
    Properties:
      ApiId: !Ref HttpApi
      IntegrationType: AWS_PROXY
      IntegrationUri: !GetAtt OrderFunction.Arn
      PayloadFormatVersion: '2.0'

  ApiRoute:
    Type: AWS::ApiGatewayV2::Route
    Properties:
      ApiId: !Ref HttpApi
      RouteKey: 'POST /orders'
      Target: !Join ['/', ['integrations', !Ref ApiIntegration]]

  ApiStage:
    Type: AWS::ApiGatewayV2::Stage
    Properties:
      ApiId: !Ref HttpApi
      StageName: '$default'
      AutoDeploy: true

  LambdaApiPermission:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !Ref OrderFunction
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${HttpApi}/*/*/orders"

Outputs:
  ApiEndpoint:
    Description: HTTP API Endpoint URL
    Value: !GetAtt HttpApi.ApiEndpoint
""",
                "solution": """# Terraform Serverless Microservice
resource "aws_dynamodb_table" "orders" {
  name         = "OrdersTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"
  attribute {
    name = "order_id"
    type = "S"
  }
}

resource "aws_iam_role" "lambda_exec" {
  name = "orders_lambda_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "dynamo_access" {
  name = "orders_dynamodb_policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:PutItem", "dynamodb:GetItem"]
      Resource = aws_dynamodb_table.orders.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "db" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.dynamo_access.arn
}

resource "aws_lambda_function" "order_fn" {
  function_name = "CreateOrderFunction"
  runtime       = "python3.12"
  handler       = "index.lambda_handler"
  role          = aws_iam_role.lambda_exec.arn
  filename      = "lambda.zip"
}

resource "aws_apigatewayv2_api" "http_api" {
  name          = "OrdersHttpApi"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integ" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.order_fn.invoke_arn
}

resource "aws_apigatewayv2_route" "post_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /orders"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integ.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}
""",
                "aws_verification_checks": [
                    {
                        "service": "apigateway",
                        "check_type": "Execute POST /orders Request",
                        "verify_prompt": "Send a curl POST request with JSON payload: curl -X POST https://<API-ENDPOINT>/orders -H 'Content-Type: application/json' -d '{\"customer\":\"Alice\",\"item\":\"Cloud Architect Guide\",\"amount\":\"49.99\"}'. Verify HTTP 201 response with generated order_id.",
                        "expected": "HTTP 201 Created with order_id"
                    },
                    {
                        "service": "dynamodb",
                        "check_type": "Verify DynamoDB Item Persistence",
                        "verify_prompt": "Open DynamoDB console > Explore items > OrdersTable. Confirm the record with matching order_id and customer 'Alice' is present.",
                        "expected": "Record persisted in DynamoDB"
                    }
                ],
                "teardown_instructions": """TEARDOWN CHECKLIST:
1. Delete API Gateway HTTP API: API Gateway console > OrdersHttpApi > Delete.
2. Delete Lambda function: Lambda console > CreateOrderFunction > Actions > Delete.
3. Delete IAM Role & Policies: IAM console > Roles > orders_lambda_exec_role > Delete.
4. Delete DynamoDB table: DynamoDB console > Tables > OrdersTable > Delete table.""",
            },

            # 4. Secure & High-Performing Edge: CloudFront + S3 + Origin Access Control (OAC)
            {
                "topic_ref": "1.6",
                "title": "Global Static Website with CloudFront, S3, and Origin Access Control (OAC)",
                "slug": "lab-aws-cloudfront-s3-oac",
                "difficulty": "intermediate",
                "estimated_time_minutes": 40,
                "estimated_cost_usd": Decimal("0.00"),
                "free_tier_eligible": True,  # 100% Free Tier (1TB CloudFront + 10M requests)
                "prerequisites": "AWS Account with S3 and CloudFront permissions.",
                "objectives": [
                    "Create an Amazon S3 bucket with Block All Public Access enabled.",
                    "Create a CloudFront distribution with Origin Access Control (OAC) enabled.",
                    "Apply an S3 bucket policy permitting read access strictly to the CloudFront distribution service principal.",
                    "Verify direct S3 access returns 403 Forbidden while CloudFront edge domain returns 200 OK."
                ],
                "topology_type": "svg",
                "topology_data": make_aws_edge_svg("Secure Global Web Delivery with CloudFront & S3 OAC"),
                "addressing_table": [
                    {"device": "CloudFront CDN", "interface": "Edge Anycast", "ip": "https://d123456789.cloudfront.net", "subnet": "Global Edge", "vlan": "CDN", "default_gateway": "N/A"},
                    {"device": "S3 Origin", "interface": "S3 REST", "ip": "my-secure-bucket.s3.us-east-1.amazonaws.com", "subnet": "Private Cloud Storage", "vlan": "Origin", "default_gateway": "N/A"},
                ],
                "step_by_step_tasks": [
                    {
                        "step_num": 1,
                        "title": "Create Private S3 Bucket and Upload Static Files",
                        "instructions": "Go to S3 > Create bucket. Ensure 'Block all public access' is CHECKED (ON). Create bucket. Upload an index.html file with sample content.",
                        "verify_prompt": "Confirm bucket has 'Bucket and objects not public' badge."
                    },
                    {
                        "step_num": 2,
                        "title": "Create CloudFront Distribution with Origin Access Control",
                        "instructions": "Go to CloudFront > Create distribution. Origin domain: select your S3 bucket. Under Origin access, select 'Origin access control settings (recommended)' > Create new OAC. Default root object: 'index.html'. Viewer protocol policy: Redirect HTTP to HTTPS.",
                        "verify_prompt": "Note the distribution domain name (e.g. d123...cloudfront.net)."
                    },
                    {
                        "step_num": 3,
                        "title": "Apply S3 Bucket Policy for CloudFront OAC",
                        "instructions": "Copy the policy generated by CloudFront. Go to S3 > Bucket > Permissions > Bucket policy > Edit. Paste the policy granting s3:GetObject with Condition StringEquals AWS:SourceArn matching your CloudFront distribution ARN.",
                        "verify_prompt": "Save bucket policy and verify syntax."
                    }
                ],
                "hints": [
                    "Exam Tip: OAC (Origin Access Control) replaces the legacy OAI (Origin Access Identity). OAC supports SSE-KMS encryption, all HTTP methods, and dynamic requests.",
                    "Gotcha: If direct S3 access returns 403 (expected) and CloudFront also returns 403, check the Default Root Object setting in CloudFront or verify the bucket policy SourceArn."
                ],
                "setup_template_type": "cloudformation",
                "setup_template": """AWSTemplateFormatVersion: '2010-09-09'
Description: 'AWS SAA-C03: CloudFront Distribution with S3 Origin and OAC'
Resources:
  StaticSiteBucket:
    Type: AWS::S3::Bucket
    Properties:
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

  OriginAccessControl:
    Type: AWS::CloudFront::OriginAccessControl
    Properties:
      OriginAccessControlConfig:
        Name: S3OACConfig
        OriginAccessControlOriginType: s3
        SigningBehavior: always
        SigningProtocol: sigv4

  CloudFrontDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Enabled: true
        DefaultRootObject: index.html
        Origins:
          - Id: S3Origin
            DomainName: !GetAtt StaticSiteBucket.RegionalDomainName
            OriginAccessControlId: !GetAtt OriginAccessControl.Id
            S3OriginConfig: {}
        DefaultCacheBehavior:
          TargetOriginId: S3Origin
          ViewerProtocolPolicy: redirect-to-https
          AllowedMethods: [GET, HEAD]
          CachedMethods: [GET, HEAD]
          ForwardedValues:
            QueryString: false
            Cookies: {Forward: none}

  BucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref StaticSiteBucket
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Sid: AllowCloudFrontServicePrincipalReadOnly
            Effect: Allow
            Principal:
              Service: cloudfront.amazonaws.com
            Action: s3:GetObject
            Resource: !Sub "${StaticSiteBucket.Arn}/*"
            Condition:
              StringEquals:
                AWS:SourceArn: !Sub "arn:aws:cloudfront::${AWS::AccountId}:distribution/${CloudFrontDistribution}"
""",
                "solution": """# Terraform CloudFront with S3 and OAC
resource "aws_s3_bucket" "site" {
  bucket_prefix = "saa-static-site-"
}

resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket = aws_s3_bucket.site.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "s3-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  default_root_object = "index.html"
  origin {
    domain_name              = aws_s3_bucket.site.bucket_regional_domain_name
    origin_id                = "S3Origin"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3Origin"
    viewer_protocol_policy = "redirect-to-https"
    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
  }
  viewer_certificate {
    cloudfront_default_certificate = true
  }
  restrictions {
    geo_restriction { restriction_type = "none" }
  }
}
""",
                "aws_verification_checks": [
                    {
                        "service": "s3",
                        "check_type": "Verify Direct S3 URL Blocked (403 Forbidden)",
                        "verify_prompt": "Try accessing the direct S3 object URL in your browser or curl: curl -I https://<BUCKET-NAME>.s3.amazonaws.com/index.html. Confirm HTTP 403 Forbidden.",
                        "expected": "HTTP/1.1 403 Forbidden"
                    },
                    {
                        "service": "cloudfront",
                        "check_type": "Verify CloudFront CDN HTTPS Delivery (200 OK)",
                        "verify_prompt": "Open the CloudFront Distribution domain in your browser: https://<DIST-ID>.cloudfront.net. Confirm site renders with HTTP 200 and 'x-cache: Hit/Miss from cloudfront' header.",
                        "expected": "HTTP/2 200 OK via CloudFront"
                    }
                ],
                "teardown_instructions": """TEARDOWN CHECKLIST:
1. CloudFront Distributions cannot be deleted while enabled. Go to CloudFront > Select Distribution > Disable (takes ~2 minutes).
2. Once status changes to 'Disabled', click Delete.
3. Go to S3 > Select your static site bucket > Empty (delete all objects) > Delete bucket.""",
            }
        ]

        for lab_info in labs_data:
            topic = Topic.objects.filter(certification=aws_cert, blueprint_ref=lab_info["topic_ref"]).first()
            if not topic:
                self.stdout.write(self.style.WARNING(f"Topic {lab_info['topic_ref']} not found for AWS. Skipping {lab_info['title']}."))
                continue

            lab, created = Lab.objects.update_or_create(
                topic=topic,
                slug=lab_info["slug"],
                defaults={
                    "title": lab_info["title"],
                    "difficulty": lab_info["difficulty"],
                    "estimated_time_minutes": lab_info["estimated_time_minutes"],
                    "estimated_cost_usd": lab_info["estimated_cost_usd"],
                    "free_tier_eligible": lab_info["free_tier_eligible"],
                    "prerequisites": lab_info["prerequisites"],
                    "objectives": lab_info["objectives"],
                    "topology_type": lab_info["topology_type"],
                    "topology_data": lab_info["topology_data"],
                    "addressing_table": lab_info["addressing_table"],
                    "step_by_step_tasks": lab_info["step_by_step_tasks"],
                    "hints": lab_info["hints"],
                    "setup_template_type": lab_info["setup_template_type"],
                    "setup_template": lab_info["setup_template"],
                    "solution": lab_info["solution"],
                    "aws_verification_checks": lab_info["aws_verification_checks"],
                    "teardown_instructions": lab_info["teardown_instructions"],
                }
            )

            status_str = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"  + {status_str} AWS Lab: {lab.title} (Topic {topic.blueprint_ref})"))

        self.stdout.write(self.style.SUCCESS("Successfully seeded comprehensive AWS architecture labs!"))
