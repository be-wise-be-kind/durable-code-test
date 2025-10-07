# Runtime Infrastructure - DNS Records
# Creates Route53 records pointing to the ALB

# A record for the main domain pointing to ALB
# Creates apex record for the environment subdomain (e.g., dev.durableaicoding.net)
# Uses the zone name directly since it's already environment-specific
resource "aws_route53_record" "main" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = local.route53_zone_id
  name    = local.route53_zone_name  # Apex: dev.durableaicoding.net
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }

  lifecycle {
    create_before_destroy = true
  }
}

# A record for www subdomain (optional)
# Creates www within the environment zone (e.g., www.dev.durableaicoding.net)
resource "aws_route53_record" "www" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = local.route53_zone_id
  name    = "www.${local.route53_zone_name}"  # www.dev.durableaicoding.net
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }

  lifecycle {
    create_before_destroy = true
  }
}

# A record for API subdomain (if using subdomain routing)
# Creates api within the environment zone (e.g., api.dev.durableaicoding.net)
resource "aws_route53_record" "api" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = local.route53_zone_id
  name    = "api.${local.route53_zone_name}"  # api.dev.durableaicoding.net
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }

  lifecycle {
    create_before_destroy = true
  }
}