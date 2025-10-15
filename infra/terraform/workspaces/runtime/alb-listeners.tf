# Purpose: ALB target groups, listeners, and routing rules for runtime services
# Scope: HTTP/HTTPS listeners, target groups for backend/frontend, and path-based routing rules
# Overview: This file defines the Application Load Balancer configuration for routing traffic to
#     ECS services. It creates target groups for backend and frontend services with health checks,
#     configures HTTP and optional HTTPS listeners on the ALB created in the base workspace, and
#     establishes path-based routing rules to direct traffic to appropriate services. The backend
#     service is accessible via /api/* paths while the frontend handles all other traffic. HTTPS
#     configuration is conditional based on the presence of an ACM certificate. Target groups use
#     the IP target type required for Fargate tasks and include deregistration delays optimized
#     for fast deployments. Health check configurations ensure service availability monitoring.
# Dependencies: Base workspace ALB, VPC, and optional ACM certificate via data sources
# Exports: Target group ARNs for ECS service integration and monitoring
# Configuration: Health check parameters and routing rules customizable via variables
# Environment: HTTPS listener only created when certificate is available
# Related: ecs.tf for service integration, data.tf for ALB and certificate lookups
# Implementation: Path-based routing with backend priority over frontend default

# Backend Target Group
resource "aws_lb_target_group" "backend" {
  name        = "${var.project_name}-${local.environment}-backend-tg"
  port        = var.backend_port
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
    timeout             = var.health_check_timeout
    interval            = var.health_check_interval
    path                = lookup(var.health_check_path, "backend", "/health")
    matcher             = "200-299"
  }

  deregistration_delay = 30

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = false
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-backend-tg"
      Service = "backend"
      Purpose = "Route traffic to backend ECS tasks"
    }
  )
}

# Frontend Target Group
resource "aws_lb_target_group" "frontend" {
  name        = "${var.project_name}-${local.environment}-frontend-tg"
  port        = var.frontend_port
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
    timeout             = var.health_check_timeout
    interval            = var.health_check_interval
    path                = lookup(var.health_check_path, "frontend", "/")
    matcher             = "200-299"
  }

  deregistration_delay = 30

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = false
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-frontend-tg"
      Service = "frontend"
      Purpose = "Route traffic to frontend ECS tasks"
    }
  )
}

# HTTP Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name     = "${var.project_name}-${local.environment}-http-listener"
      Protocol = "HTTP"
      Purpose  = "Handle HTTP traffic"
    }
  )
}

# HTTPS Listener (conditional - only if certificate exists)
resource "aws_lb_listener" "https" {
  count = var.domain_name != "" && length(data.aws_acm_certificate.main) > 0 ? 1 : 0

  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = data.aws_acm_certificate.main[0].arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name     = "${var.project_name}-${local.environment}-https-listener"
      Protocol = "HTTPS"
      Purpose  = "Handle HTTPS traffic"
    }
  )
}

# HTTP Listener Rule for Backend API
resource "aws_lb_listener_rule" "backend_http" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/docs*", "/openapi.json", "/redoc", "/health"]
    }
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-backend-http-rule"
      Service = "backend"
      Purpose = "Route API traffic to backend"
    }
  )
}

# HTTPS Listener Rule for Backend API (conditional)
resource "aws_lb_listener_rule" "backend_https" {
  count = var.domain_name != "" && length(data.aws_acm_certificate.main) > 0 ? 1 : 0

  listener_arn = aws_lb_listener.https[0].arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/docs*", "/openapi.json", "/redoc", "/health"]
    }
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-backend-https-rule"
      Service = "backend"
      Purpose = "Route API traffic to backend via HTTPS"
    }
  )
}

# HTTP to HTTPS Redirect (conditional - only if certificate exists)
resource "aws_lb_listener_rule" "http_to_https_redirect" {
  count = var.domain_name != "" && length(data.aws_acm_certificate.main) > 0 ? 1 : 0

  listener_arn = aws_lb_listener.http.arn
  priority     = 50

  action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  condition {
    host_header {
      values = [var.domain_name]
    }
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name    = "${var.project_name}-${local.environment}-http-redirect"
      Purpose = "Redirect HTTP to HTTPS"
    }
  )
}