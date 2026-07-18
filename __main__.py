import pulumi
import pulumi_aws as aws
import json

# Configuration
config = pulumi.Config()
project_name = "aws-transit-gateway"
environment = "dev"

# Common tags
common_tags = {
    "Project": "aws-transit-gateway",
    "Environment": environment,
    "ManagedBy": "Pulumi"
}

#=============================================================================
# VPC-A: Entry point VPC with bastion server
#=============================================================================

# Create VPC-A
vpc_a = aws.ec2.Vpc(f"{project_name}-vpc-a",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={**common_tags, "Name": f"{project_name}-vpc-a"}
)

# Internet Gateway for VPC-A
igw_a = aws.ec2.InternetGateway(f"{project_name}-igw-a",
    vpc_id=vpc_a.id,
    tags={**common_tags, "Name": f"{project_name}-igw-a"}
)

# Public Subnet in VPC-A (for bastion server)
public_subnet_a = aws.ec2.Subnet(f"{project_name}-public-subnet-a",
    vpc_id=vpc_a.id,
    cidr_block="10.0.1.0/24",
    availability_zone="ap-southeast-1a",
    map_public_ip_on_launch=True,
    tags={**common_tags, "Name": f"{project_name}-public-subnet-a"}
)

# Transit Gateway Subnet in VPC-A
tgw_subnet_a = aws.ec2.Subnet(f"{project_name}-tgw-subnet-a",
    vpc_id=vpc_a.id,
    cidr_block="10.0.2.0/28",
    availability_zone="ap-southeast-1a",
    tags={**common_tags, "Name": f"{project_name}-tgw-subnet-a", "Purpose": "TransitGateway"}
)

#=============================================================================
# VPC-B: Application VPC
#=============================================================================

# Create VPC-B
vpc_b = aws.ec2.Vpc(f"{project_name}-vpc-b",
    cidr_block="10.1.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={**common_tags, "Name": f"{project_name}-vpc-b"}
)

# Private Subnet in VPC-B
private_subnet_b = aws.ec2.Subnet(f"{project_name}-private-subnet-b",
    vpc_id=vpc_b.id,
    cidr_block="10.1.1.0/24",
    availability_zone="ap-southeast-1a",
    tags={**common_tags, "Name": f"{project_name}-private-subnet-b"}
)

# Transit Gateway Subnet in VPC-B
tgw_subnet_b = aws.ec2.Subnet(f"{project_name}-tgw-subnet-b",
    vpc_id=vpc_b.id,
    cidr_block="10.1.2.0/28",
    availability_zone="ap-southeast-1a",
    tags={**common_tags, "Name": f"{project_name}-tgw-subnet-b", "Purpose": "TransitGateway"}
)

#=============================================================================
# VPC-C: Application VPC
#=============================================================================

# Create VPC-C
vpc_c = aws.ec2.Vpc(f"{project_name}-vpc-c",
    cidr_block="10.2.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={**common_tags, "Name": f"{project_name}-vpc-c"}
)

# Private Subnet in VPC-C
private_subnet_c = aws.ec2.Subnet(f"{project_name}-private-subnet-c",
    vpc_id=vpc_c.id,
    cidr_block="10.2.1.0/24",
    availability_zone="ap-southeast-1a",
    tags={**common_tags, "Name": f"{project_name}-private-subnet-c"}
)

# Transit Gateway Subnet in VPC-C
tgw_subnet_c = aws.ec2.Subnet(f"{project_name}-tgw-subnet-c",
    vpc_id=vpc_c.id,
    cidr_block="10.2.2.0/28",
    availability_zone="ap-southeast-1a",
    tags={**common_tags, "Name": f"{project_name}-tgw-subnet-c", "Purpose": "TransitGateway"}
)

#=============================================================================
# Transit Gateway
#=============================================================================

# Create Transit Gateway
transit_gateway = aws.ec2transitgateway.TransitGateway(f"{project_name}-tgw",
    description="Lab Transit Gateway for VPC connectivity",
    amazon_side_asn=64512,
    dns_support="enable",
    vpn_ecmp_support="enable",
    default_route_table_association="enable",
    default_route_table_propagation="enable",
    auto_accept_shared_attachments="disable",
    tags={**common_tags, "Name": f"{project_name}-transit-gateway"}
)

# Attach VPC-A to Transit Gateway
tgw_attachment_a = aws.ec2transitgateway.VpcAttachment(f"{project_name}-tgw-att-a",
    transit_gateway_id=transit_gateway.id,
    vpc_id=vpc_a.id,
    subnet_ids=[tgw_subnet_a.id],
    dns_support="enable",
    tags={**common_tags, "Name": f"{project_name}-tgw-attachment-a"}
)

# Attach VPC-B to Transit Gateway
tgw_attachment_b = aws.ec2transitgateway.VpcAttachment(f"{project_name}-tgw-att-b",
    transit_gateway_id=transit_gateway.id,
    vpc_id=vpc_b.id,
    subnet_ids=[tgw_subnet_b.id],
    dns_support="enable",
    tags={**common_tags, "Name": f"{project_name}-tgw-attachment-b"}
)

# Attach VPC-C to Transit Gateway
tgw_attachment_c = aws.ec2transitgateway.VpcAttachment(f"{project_name}-tgw-att-c",
    transit_gateway_id=transit_gateway.id,
    vpc_id=vpc_c.id,
    subnet_ids=[tgw_subnet_c.id],
    dns_support="enable",
    tags={**common_tags, "Name": f"{project_name}-tgw-attachment-c"}
)

#=============================================================================
# Route Tables
#=============================================================================

# Public Route Table for VPC-A
public_route_table_a = aws.ec2.RouteTable(f"{project_name}-public-rt-a",
    vpc_id=vpc_a.id,
    tags={**common_tags, "Name": f"{project_name}-public-route-table-a"}
)

# Route to Internet Gateway
aws.ec2.Route(f"{project_name}-igw-route-a",
    route_table_id=public_route_table_a.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=igw_a.id
)

# Routes to other VPCs via Transit Gateway
aws.ec2.Route(f"{project_name}-tgw-route-a-to-b",
    route_table_id=public_route_table_a.id,
    destination_cidr_block="10.1.0.0/16",
    transit_gateway_id=transit_gateway.id,
    opts=pulumi.ResourceOptions(depends_on=[tgw_attachment_a, tgw_attachment_b])
)

aws.ec2.Route(f"{project_name}-tgw-route-a-to-c",
    route_table_id=public_route_table_a.id,
    destination_cidr_block="10.2.0.0/16",
    transit_gateway_id=transit_gateway.id,
    opts=pulumi.ResourceOptions(depends_on=[tgw_attachment_a, tgw_attachment_c])
)

# Associate public subnet with route table
aws.ec2.RouteTableAssociation(f"{project_name}-public-rt-assoc-a",
    subnet_id=public_subnet_a.id,
    route_table_id=public_route_table_a.id
)

# Private Route Table for VPC-B
private_route_table_b = aws.ec2.RouteTable(f"{project_name}-private-rt-b",
    vpc_id=vpc_b.id,
    tags={**common_tags, "Name": f"{project_name}-private-route-table-b"}
)

# Routes to other VPCs via Transit Gateway
aws.ec2.Route(f"{project_name}-tgw-route-b-to-a",
    route_table_id=private_route_table_b.id,
    destination_cidr_block="10.0.0.0/16",
    transit_gateway_id=transit_gateway.id,
    opts=pulumi.ResourceOptions(depends_on=[tgw_attachment_b, tgw_attachment_a])
)

aws.ec2.Route(f"{project_name}-tgw-route-b-to-c",
    route_table_id=private_route_table_b.id,
    destination_cidr_block="10.2.0.0/16",
    transit_gateway_id=transit_gateway.id,
    opts=pulumi.ResourceOptions(depends_on=[tgw_attachment_b, tgw_attachment_c])
)

# Associate private subnet with route table
aws.ec2.RouteTableAssociation(f"{project_name}-private-rt-assoc-b",
    subnet_id=private_subnet_b.id,
    route_table_id=private_route_table_b.id
)

# Private Route Table for VPC-C
private_route_table_c = aws.ec2.RouteTable(f"{project_name}-private-rt-c",
    vpc_id=vpc_c.id,
    tags={**common_tags, "Name": f"{project_name}-private-route-table-c"}
)

# Routes to other VPCs via Transit Gateway
aws.ec2.Route(f"{project_name}-tgw-route-c-to-a",
    route_table_id=private_route_table_c.id,
    destination_cidr_block="10.0.0.0/16",
    transit_gateway_id=transit_gateway.id,
    opts=pulumi.ResourceOptions(depends_on=[tgw_attachment_c, tgw_attachment_a])
)

aws.ec2.Route(f"{project_name}-tgw-route-c-to-b",
    route_table_id=private_route_table_c.id,
    destination_cidr_block="10.1.0.0/16",
    transit_gateway_id=transit_gateway.id,
    opts=pulumi.ResourceOptions(depends_on=[tgw_attachment_c, tgw_attachment_b])
)

# Associate private subnet with route table
aws.ec2.RouteTableAssociation(f"{project_name}-private-rt-assoc-c",
    subnet_id=private_subnet_c.id,
    route_table_id=private_route_table_c.id
)

#=============================================================================
# Security Groups
#=============================================================================

# Security Group for Bastion Server
bastion_sg = aws.ec2.SecurityGroup(f"{project_name}-bastion-sg",
    description="Security group for bastion server",
    vpc_id=vpc_a.id,
    ingress=[
        # SSH access from anywhere (restrict to your IP in production)
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"]
        ),
        # ICMP for ping tests
        aws.ec2.SecurityGroupIngressArgs(
            protocol="icmp",
            from_port=-1,
            to_port=-1,
            cidr_blocks=["10.0.0.0/8"]
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={**common_tags, "Name": f"{project_name}-bastion-sg"}
)

# Security Group for Private Instances
private_sg = aws.ec2.SecurityGroup(f"{project_name}-private-sg",
    description="Security group for private instances",
    vpc_id=vpc_b.id,  # We'll use this SG for both VPC-B and VPC-C instances
    ingress=[
        # SSH access from all VPCs
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["10.0.0.0/8"]
        ),
        # ICMP for ping tests
        aws.ec2.SecurityGroupIngressArgs(
            protocol="icmp",
            from_port=-1,
            to_port=-1,
            cidr_blocks=["10.0.0.0/8"]
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={**common_tags, "Name": f"{project_name}-private-sg"}
)

# Security Group for VPC-C (referencing the same rules)
private_sg_c = aws.ec2.SecurityGroup(f"{project_name}-private-sg-c",
    description="Security group for private instances in VPC-C",
    vpc_id=vpc_c.id,
    ingress=[
        # SSH access from all VPCs
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["10.0.0.0/8"]
        ),
        # ICMP for ping tests
        aws.ec2.SecurityGroupIngressArgs(
            protocol="icmp",
            from_port=-1,
            to_port=-1,
            cidr_blocks=["10.0.0.0/8"]
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={**common_tags, "Name": f"{project_name}-private-sg-c"}
)

#=============================================================================
# EC2 Instances
#=============================================================================

# Bastion Server in VPC-A
bastion_instance = aws.ec2.Instance(f"{project_name}-bastion",
    instance_type="t2.micro",
    ami='ami-01811d4912b4ccb26',
    key_name="tgw-key",
    vpc_security_group_ids=[bastion_sg.id],
    subnet_id=public_subnet_a.id,
    associate_public_ip_address=True,
    user_data="""#!/bin/bash
    sudo apt update -y
    sudo apt install -y htop
    """,
    tags={**common_tags, "Name": f"{project_name}-bastion-server"}
)

# EC2 Instance in VPC-B
instance_b = aws.ec2.Instance(f"{project_name}-instance-b",
    instance_type="t2.micro",
    ami='ami-01811d4912b4ccb26',
    key_name="tgw-key",
    vpc_security_group_ids=[private_sg.id],
    subnet_id=private_subnet_b.id,
    user_data="""#!/bin/bash
    sudo apt update -y
    sudo apt install -y htop
    """,
    tags={**common_tags, "Name": f"{project_name}-instance-vpc-b"}
)

# EC2 Instance in VPC-C
instance_c = aws.ec2.Instance(f"{project_name}-instance-c",
    instance_type="t2.micro",
    ami='ami-01811d4912b4ccb26',
    key_name="tgw-key",
    vpc_security_group_ids=[private_sg_c.id],
    subnet_id=private_subnet_c.id,
    user_data="""#!/bin/bash
    sudo apt update -y
    sudo apt install -y htop
    """,
    tags={**common_tags, "Name": f"{project_name}-instance-vpc-c"}
)

#=============================================================================
# Outputs
#=============================================================================

# Export important values
pulumi.export("vpc_a_id", vpc_a.id)
pulumi.export("vpc_b_id", vpc_b.id)
pulumi.export("vpc_c_id", vpc_c.id)
pulumi.export("transit_gateway_id", transit_gateway.id)
pulumi.export("bastion_public_ip", bastion_instance.public_ip)
pulumi.export("bastion_private_ip", bastion_instance.private_ip)
pulumi.export("instance_b_private_ip", instance_b.private_ip)
pulumi.export("instance_c_private_ip", instance_c.private_ip)

# Export connection information
pulumi.export("ssh_command_bastion", pulumi.Output.concat(
    "ssh -i tgw-key.pem ubuntu@", bastion_instance.public_ip
))

pulumi.export("architecture_summary", {
    "vpc_a": "10.0.0.0/16 (Entry Point VPC)",
    "vpc_b": "10.1.0.0/16 (Application VPC 1)",
    "vpc_c": "10.2.0.0/16 (Application VPC 2)",
    "transit_gateway": "Connects all VPCs",
    "bastion_access": "SSH via public IP to access the private instances"
})
