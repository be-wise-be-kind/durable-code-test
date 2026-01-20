# Runtime Infrastructure - Networking Resources (Cost Optimized)
# These are expensive resources that can be destroyed nightly for cost savings

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? var.az_count : 0

  domain     = "vpc"
  depends_on = [data.aws_internet_gateway.main]

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name = "${var.project_name}-${local.environment}-nat-eip-${count.index + 1}"
      Type = "nat-gateway"
    }
  )
}

# NAT Gateways (expensive - moved to runtime for cost optimization)
resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? var.az_count : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = data.aws_subnets.public.ids[count.index]

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name = "${var.project_name}-${local.environment}-nat-${count.index + 1}"
      Type = "nat-gateway"
    }
  )

  depends_on = [data.aws_internet_gateway.main]
}

# Route Tables - Private (always created for VPC endpoints and subnet routing)
resource "aws_route_table" "private" {
  count = var.az_count

  vpc_id = data.aws_vpc.main.id

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name = "${var.project_name}-${local.environment}-private-rt-${count.index + 1}"
      Type = "route-table"
    }
  )
}

# NAT Gateway route (only when NAT Gateway is enabled)
resource "aws_route" "nat_gateway" {
  count = var.enable_nat_gateway ? var.az_count : 0

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[count.index].id
}

# Route Table Associations - Private (always needed for private subnet routing)
resource "aws_route_table_association" "private" {
  count = var.az_count

  subnet_id      = data.aws_subnets.private.ids[count.index]
  route_table_id = aws_route_table.private[count.index].id
}

# VPC Endpoints Security Group (for private subnets without NAT Gateway)
resource "aws_security_group" "vpc_endpoints" {
  count = !var.enable_nat_gateway ? 1 : 0

  name        = "${var.project_name}-${local.environment}-vpc-endpoints-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-vpc-endpoints-sg"
      Type      = "security-group"
      Component = "vpc-endpoints"
    }
  )
}

# VPC Endpoints (for cost optimization when NAT Gateway is disabled)

# S3 VPC Endpoint (Gateway type - no cost)
resource "aws_vpc_endpoint" "s3" {
  count = !var.enable_nat_gateway ? 1 : 0

  vpc_id            = data.aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.private[*].id

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-s3-endpoint"
      Type    = "vpc-endpoint"
      Service = "s3"
    }
  )
}

# ECR API VPC Endpoint (Interface type)
resource "aws_vpc_endpoint" "ecr_api" {
  count = !var.enable_nat_gateway ? 1 : 0

  vpc_id              = data.aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.aws_subnets.private.ids
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-ecr-api-endpoint"
      Type    = "vpc-endpoint"
      Service = "ecr-api"
    }
  )
}

# ECR Docker VPC Endpoint (Interface type)
resource "aws_vpc_endpoint" "ecr_dkr" {
  count = !var.enable_nat_gateway ? 1 : 0

  vpc_id              = data.aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.aws_subnets.private.ids
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-ecr-dkr-endpoint"
      Type    = "vpc-endpoint"
      Service = "ecr-dkr"
    }
  )
}

# CloudWatch Logs VPC Endpoint (Interface type)
resource "aws_vpc_endpoint" "logs" {
  count = !var.enable_nat_gateway ? 1 : 0

  vpc_id              = data.aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = data.aws_subnets.private.ids
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-logs-endpoint"
      Type    = "vpc-endpoint"
      Service = "cloudwatch-logs"
    }
  )
}