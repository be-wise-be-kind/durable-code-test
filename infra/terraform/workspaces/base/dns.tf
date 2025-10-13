# Base Infrastructure - Route53 and ACM Configuration
# These are persistent resources for DNS and SSL certificates

# Route53 Hosted Zone (only created when domain is configured)
resource "aws_route53_zone" "main" {
  count = var.domain_name != "" && var.create_route53_zone ? 1 : 0

  name    = var.domain_name
  comment = "Hosted zone for ${var.project_name} ${local.environment} environment"

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name        = "${var.project_name}-${local.environment}-zone"
      Domain      = var.domain_name
      Environment = local.environment
    }
  )
}

# Delegation record in apex zone (creates NS record pointing to subdomain zone)
resource "aws_route53_record" "zone_delegation" {
  count = var.domain_name != "" && var.create_route53_zone && var.apex_zone_id != "" ? 1 : 0

  zone_id = var.apex_zone_id
  name    = var.domain_name
  type    = "NS"
  ttl     = 300

  records = aws_route53_zone.main[0].name_servers

  lifecycle {
    create_before_destroy = true # Update delegation before deleting old record if zone recreated
  }

  depends_on = [aws_route53_zone.main]
}

# ACM Certificate for the primary domain (only when domain is configured)
resource "aws_acm_certificate" "main" {
  count = var.domain_name != "" && var.create_route53_zone ? 1 : 0

  domain_name = var.domain_name
  subject_alternative_names = [
    "*.${var.domain_name}",                       # Wildcard for subdomains
    "${local.environment}.${var.domain_name}",    # Environment-specific subdomain
    "api.${var.domain_name}",                     # API subdomain
    "api-${local.environment}.${var.domain_name}" # Environment-specific API
  ]

  validation_method = "DNS" # DNS validation for automation

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name        = "${var.project_name}-${local.environment}-certificate"
      Domain      = var.domain_name
      Environment = local.environment
    }
  )
}

# Route53 record for certificate validation
resource "aws_route53_record" "cert_validation" {
  for_each = var.domain_name != "" && var.create_route53_zone ? {
    for dvo in aws_acm_certificate.main[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.main[0].zone_id

  depends_on = [aws_route53_zone.main]
}

# Certificate validation
resource "aws_acm_certificate_validation" "main" {
  count = var.domain_name != "" && var.create_route53_zone ? 1 : 0

  certificate_arn         = aws_acm_certificate.main[0].arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]

  depends_on = [aws_route53_record.cert_validation]
}