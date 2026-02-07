# Purpose: ECS cluster, task definitions, and services for containerized application runtime
# Scope: Runtime ECS resources including cluster, tasks, services, IAM roles, and CloudWatch logs
# Overview: This file defines the ephemeral ECS infrastructure for running containerized frontend
#     and backend services on AWS Fargate. It creates an ECS cluster with optional Container Insights,
#     task definitions with environment-specific resource allocations, and services integrated with
#     the Application Load Balancer. The configuration includes IAM roles for task execution and
#     application permissions, CloudWatch log groups for container output, and optional auto-scaling
#     policies. Resources reference base infrastructure via data sources, enabling independent
#     lifecycle management. The setup emphasizes cost optimization through Fargate Spot usage in
#     non-production environments and minimal resource allocation based on actual requirements.
# Dependencies: Base workspace VPC, subnets, security groups, ECR repositories, and ALB via data sources
# Exports: ECS cluster ARN, service names, task definition ARNs for monitoring and operations
# Configuration: Environment-specific sizing via variables, feature flags for optional capabilities
# Environment: Resource allocation and features vary by environment (dev/staging/prod)
# Related: data.tf for base resource lookups, alb-listeners.tf for load balancer integration
# Implementation: Uses Fargate launch type with optional Fargate Spot for cost optimization

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${local.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-cluster"
      Component = "ecs-cluster"
      Purpose   = "Container orchestration platform"
    }
  )
}

# ECS Cluster Capacity Providers
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = var.environment == "prod" ? "FARGATE" : "FARGATE_SPOT"
    weight            = 100
    base              = 1
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}-${local.environment}/backend"
  retention_in_days = lookup(var.log_retention_days, var.environment, 7)
  kms_key_id        = data.terraform_remote_state.base.outputs.kms_logs_key_arn

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-backend-logs"
      Service   = "backend"
      Component = "logging"
    }
  )
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.project_name}-${local.environment}/frontend"
  retention_in_days = lookup(var.log_retention_days, var.environment, 7)
  kms_key_id        = data.terraform_remote_state.base.outputs.kms_logs_key_arn

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-frontend-logs"
      Service   = "frontend"
      Component = "logging"
    }
  )
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-${local.environment}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-ecs-task-execution"
      Purpose = "ECS task execution role"
    }
  )
}

# Attach managed policy for ECS task execution
resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for ECR access and logging
resource "aws_iam_role_policy" "ecs_task_execution_additional" {
  name = "${var.project_name}-${local.environment}-ecs-task-execution-additional"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          aws_cloudwatch_log_group.backend.arn,
          "${aws_cloudwatch_log_group.backend.arn}:*",
          aws_cloudwatch_log_group.frontend.arn,
          "${aws_cloudwatch_log_group.frontend.arn}:*"
        ]
      }
    ]
  })
}

# IAM Role for ECS Tasks (application permissions)
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-${local.environment}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-ecs-task"
      Purpose = "ECS task application role"
    }
  )
}

# Policy for ECS Exec (debugging)
resource "aws_iam_role_policy" "ecs_exec" {
  count = var.enable_ecs_exec ? 1 : 0
  name  = "${var.project_name}-${local.environment}-ecs-exec"
  role  = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ]
        Resource = "*"
      }
    ]
  })
}

# Backend Task Definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-${local.environment}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = lookup(var.ecs_task_cpu, var.environment, "256")
  memory                   = lookup(var.ecs_task_memory, var.environment, "512")
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${data.aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = var.backend_port
          protocol      = "tcp"
        }
      ]

      environment = concat([
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "PORT"
          value = tostring(var.backend_port)
        }
        ], var.enable_observability ? [
        {
          name  = "OTEL_ENABLED"
          value = "true"
        },
        {
          name  = "OTEL_SERVICE_NAME"
          value = "${var.project_name}-backend"
        },
        {
          name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
          value = "http://${aws_instance.observability[0].private_ip}:4317"
        },
        {
          name  = "OTEL_TRACES_SAMPLER"
          value = "traceidratio"
        },
        {
          name  = "OTEL_TRACES_SAMPLER_ARG"
          value = var.environment == "prod" ? "0.1" : "1.0"
        },
        {
          name  = "PYROSCOPE_ENABLED"
          value = "true"
        },
        {
          name  = "PYROSCOPE_SERVER_ADDRESS"
          value = "http://${aws_instance.observability[0].private_ip}:4040"
        }
      ] : [])

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:${var.backend_port}${lookup(var.health_check_path, "backend", "/health")}')\" || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      linuxParameters = var.enable_ecs_exec ? {
        initProcessEnabled = true
      } : null
    }
  ])

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-backend-task"
      Service = "backend"
    }
  )
}

# Frontend Task Definition
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.project_name}-${local.environment}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = lookup(var.ecs_task_cpu, var.environment, "256")
  memory                   = lookup(var.ecs_task_memory, var.environment, "512")
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${data.aws_ecr_repository.frontend.repository_url}:${var.frontend_image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = var.frontend_port
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "PORT"
          value = tostring(var.frontend_port)
        },
        {
          name  = "BACKEND_URL"
          value = "http://${aws_lb.main.dns_name}/api"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.frontend_port}${lookup(var.health_check_path, "frontend", "/")} || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      linuxParameters = var.enable_ecs_exec ? {
        initProcessEnabled = true
      } : null
    }
  ])

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-frontend-task"
      Service = "frontend"
    }
  )
}

# Backend ECS Service
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-${local.environment}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = lookup(var.ecs_service_desired_count, var.environment, 1)
  launch_type     = "FARGATE"

  enable_ecs_managed_tags = true
  enable_execute_command  = var.enable_ecs_exec

  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = [data.aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = var.backend_port
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-backend-service"
      Service = "backend"
    }
  )

  depends_on = [aws_lb_listener.http]
}

# Frontend ECS Service
resource "aws_ecs_service" "frontend" {
  name            = "${var.project_name}-${local.environment}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = lookup(var.ecs_service_desired_count, var.environment, 1)
  launch_type     = "FARGATE"

  enable_ecs_managed_tags = true
  enable_execute_command  = var.enable_ecs_exec

  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = [data.aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = var.frontend_port
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-frontend-service"
      Service = "frontend"
    }
  )

  depends_on = [aws_lb_listener.http]
}