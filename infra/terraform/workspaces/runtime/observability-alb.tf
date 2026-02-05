# Purpose: ALB target groups, attachments, and listener rules for observability services
# Scope: Grafana UI and Alloy Faro receiver routing through the runtime ALB
# Overview: Configures ALB routing for the observability stack running on the EC2 instance. Creates
#     target groups for Grafana (port 3001) and Alloy Faro receiver (port 12347) using instance-type
#     targets (unlike ECS Fargate ip-type targets). Attaches the observability EC2 instance to both
#     target groups and creates HTTP/HTTPS listener rules for path-based routing: /grafana/* at
#     priority 90 and /collect/* at priority 91. These priorities sit below the HTTP-to-HTTPS redirect
#     (50) and above the backend API rule (100), ensuring observability routes are evaluated before the
#     API catch-all. All resources are conditional on the enable_observability feature flag. HTTPS rules
#     additionally require a valid domain and ACM certificate.
# Dependencies: Runtime ALB (alb.tf), HTTP/HTTPS listeners (alb-listeners.tf), observability EC2 (observability-ec2.tf)
# Exports: Target group ARNs for monitoring and operational visibility
# Configuration: Health check paths and intervals use standard values matching service endpoints
# Environment: Identical routing configuration across dev/staging/prod environments
# Related: observability-ec2.tf for EC2 instance, alb-listeners.tf for listener references
# Implementation: Instance-type target groups with path-based ALB routing and conditional HTTPS support

# Grafana Target Group
resource "aws_lb_target_group" "grafana" {
  count = var.enable_observability ? 1 : 0

  name        = "${var.project_name}-${local.environment}-grafana-tg"
  port        = 3001
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "instance"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/grafana/api/health"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-grafana-tg"
      Component = "observability"
      Service   = "grafana"
      Purpose   = "Route traffic to Grafana UI"
    }
  )
}

# Alloy Faro Target Group
resource "aws_lb_target_group" "alloy_faro" {
  count = var.enable_observability ? 1 : 0

  name        = "${var.project_name}-${local.environment}-faro-tg"
  port        = 12347
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "instance"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/-/ready"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-faro-tg"
      Component = "observability"
      Service   = "alloy-faro"
      Purpose   = "Route traffic to Alloy Faro receiver"
    }
  )
}

# Grafana Target Group Attachment
resource "aws_lb_target_group_attachment" "grafana" {
  count = var.enable_observability ? 1 : 0

  target_group_arn = aws_lb_target_group.grafana[0].arn
  target_id        = aws_instance.observability[0].id
  port             = 3001
}

# Alloy Faro Target Group Attachment
resource "aws_lb_target_group_attachment" "alloy_faro" {
  count = var.enable_observability ? 1 : 0

  target_group_arn = aws_lb_target_group.alloy_faro[0].arn
  target_id        = aws_instance.observability[0].id
  port             = 12347
}

# HTTP Listener Rule - Grafana UI
resource "aws_lb_listener_rule" "grafana_http" {
  count = var.enable_observability ? 1 : 0

  listener_arn = aws_lb_listener.http.arn
  priority     = 90

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.grafana[0].arn
  }

  condition {
    path_pattern {
      values = ["/grafana/*"]
    }
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-grafana-http-rule"
      Component = "observability"
      Service   = "grafana"
      Purpose   = "Route Grafana traffic via HTTP"
    }
  )
}

# HTTP Listener Rule - Alloy Faro Receiver
resource "aws_lb_listener_rule" "faro_http" {
  count = var.enable_observability ? 1 : 0

  listener_arn = aws_lb_listener.http.arn
  priority     = 91

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.alloy_faro[0].arn
  }

  condition {
    path_pattern {
      values = ["/collect/*"]
    }
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-faro-http-rule"
      Component = "observability"
      Service   = "alloy-faro"
      Purpose   = "Route Faro telemetry traffic via HTTP"
    }
  )
}

# HTTPS Listener Rule - Grafana UI (conditional on certificate AND observability)
resource "aws_lb_listener_rule" "grafana_https" {
  count = var.enable_observability && var.domain_name != "" && length(data.aws_acm_certificate.main) > 0 ? 1 : 0

  listener_arn = aws_lb_listener.https[0].arn
  priority     = 90

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.grafana[0].arn
  }

  condition {
    path_pattern {
      values = ["/grafana/*"]
    }
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-grafana-https-rule"
      Component = "observability"
      Service   = "grafana"
      Purpose   = "Route Grafana traffic via HTTPS"
    }
  )
}

# HTTPS Listener Rule - Alloy Faro Receiver (conditional on certificate AND observability)
resource "aws_lb_listener_rule" "faro_https" {
  count = var.enable_observability && var.domain_name != "" && length(data.aws_acm_certificate.main) > 0 ? 1 : 0

  listener_arn = aws_lb_listener.https[0].arn
  priority     = 91

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.alloy_faro[0].arn
  }

  condition {
    path_pattern {
      values = ["/collect/*"]
    }
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name      = "${var.project_name}-${local.environment}-faro-https-rule"
      Component = "observability"
      Service   = "alloy-faro"
      Purpose   = "Route Faro telemetry traffic via HTTPS"
    }
  )
}
