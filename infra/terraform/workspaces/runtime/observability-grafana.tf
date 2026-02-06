# Purpose: Grafana datasources, dashboards, and organization preferences managed via Terraform provider
# Scope: Grafana API-managed resources for the observability stack, conditional on enable_observability
# Overview: Provisions Grafana datasources, dashboards, and organization preferences using the Grafana
#     Terraform provider instead of file-based provisioning. This approach pushes configuration via the
#     Grafana HTTP API after the EC2 instance and Grafana container are running, avoiding user-data size
#     constraints and ensuring dashboards are deployed to the running instance. Four datasources cover
#     all observability pillars (Mimir for metrics, Loki for logs, Tempo for traces, Pyroscope for
#     profiles) with cross-pillar correlation configured. Seven dashboards are loaded from JSON files
#     in infra/observability/grafana/dashboards/. Organization preferences set the home dashboard.
#     All resources depend on the EC2 instance, ALB target group attachment, and listener rule to ensure
#     Grafana is reachable before the provider attempts API calls.
# Dependencies: Grafana provider, observability EC2 instance, ALB routing, dashboard JSON files
# Exports: Grafana datasource and dashboard resources for observability visualization
# Configuration: Datasource URLs use Docker Compose service hostnames (resolved inside the container network)
# Environment: Identical configuration across dev/staging/prod environments
# Related: observability-ec2.tf for EC2 instance, observability-alb.tf for ALB routing, datasources.yml as reference
# Implementation: Grafana provider API calls with dependency chain ensuring correct resource ordering

# -----------------------------------------------------------------------------
# Datasources
# -----------------------------------------------------------------------------

resource "grafana_data_source" "mimir" {
  count = var.enable_observability ? 1 : 0

  type       = "prometheus"
  name       = "Mimir"
  uid        = "mimir"
  url        = "http://mimir:9009/prometheus"
  is_default = true

  json_data_encoded = jsonencode({
    httpMethod = "POST"
    exemplarTraceIdDestinations = [
      {
        name          = "traceID"
        datasourceUid = "tempo"
      }
    ]
  })

  depends_on = [
    aws_instance.observability,
    aws_lb_target_group_attachment.grafana,
    aws_lb_listener_rule.grafana_http,
  ]
}

resource "grafana_data_source" "loki" {
  count = var.enable_observability ? 1 : 0

  type = "loki"
  name = "Loki"
  uid  = "loki"
  url  = "http://loki:3100"

  json_data_encoded = jsonencode({
    derivedFields = [
      {
        name          = "TraceID"
        matcherRegex  = "\"trace_id\":\"(\\w+)\""
        url           = "$${__value.raw}"
        datasourceUid = "tempo"
        matcherType   = "regex"
      }
    ]
  })

  depends_on = [
    aws_instance.observability,
    aws_lb_target_group_attachment.grafana,
    aws_lb_listener_rule.grafana_http,
  ]
}

resource "grafana_data_source" "tempo" {
  count = var.enable_observability ? 1 : 0

  type = "tempo"
  name = "Tempo"
  uid  = "tempo"
  url  = "http://tempo:3200"

  json_data_encoded = jsonencode({
    tracesToLogsV2 = {
      datasourceUid   = "loki"
      filterByTraceID = true
      filterBySpanID  = false
      tags = [
        {
          key   = "service.name"
          value = "service_name"
        }
      ]
    }
    tracesToMetrics = {
      datasourceUid = "mimir"
      tags = [
        {
          key   = "service.name"
          value = "service"
        }
      ]
    }
    tracesToProfiles = {
      datasourceUid = "pyroscope"
      tags = [
        {
          key   = "service.name"
          value = "service_name"
        }
      ]
      profileTypeId = "process_cpu:cpu:nanoseconds:cpu:nanoseconds"
    }
    nodeGraph = {
      enabled = true
    }
    serviceMap = {
      datasourceUid = "mimir"
    }
  })

  depends_on = [
    aws_instance.observability,
    aws_lb_target_group_attachment.grafana,
    aws_lb_listener_rule.grafana_http,
  ]
}

resource "grafana_data_source" "pyroscope" {
  count = var.enable_observability ? 1 : 0

  type = "grafana-pyroscope-datasource"
  name = "Pyroscope"
  uid  = "pyroscope"
  url  = "http://pyroscope:4040"

  depends_on = [
    aws_instance.observability,
    aws_lb_target_group_attachment.grafana,
    aws_lb_listener_rule.grafana_http,
  ]
}

# -----------------------------------------------------------------------------
# Dashboards
# -----------------------------------------------------------------------------

locals {
  dashboard_path = "${path.module}/../../../observability/grafana/dashboards"
}

resource "grafana_dashboard" "home" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/home.json")

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.loki,
    grafana_data_source.tempo,
    grafana_data_source.pyroscope,
  ]
}

resource "grafana_dashboard" "golden_signals" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/golden-signals-overview.json")

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.loki,
    grafana_data_source.tempo,
    grafana_data_source.pyroscope,
  ]
}

resource "grafana_dashboard" "backend_red" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/backend-red-method.json")

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.loki,
    grafana_data_source.tempo,
    grafana_data_source.pyroscope,
  ]
}

resource "grafana_dashboard" "frontend_vitals" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/frontend-web-vitals.json")

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.loki,
    grafana_data_source.tempo,
    grafana_data_source.pyroscope,
  ]
}

resource "grafana_dashboard" "infrastructure_use" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/infrastructure-use-method.json")

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.loki,
    grafana_data_source.tempo,
    grafana_data_source.pyroscope,
  ]
}

resource "grafana_dashboard" "trace_analysis" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/trace-analysis.json")

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.loki,
    grafana_data_source.tempo,
    grafana_data_source.pyroscope,
  ]
}

resource "grafana_dashboard" "profiling" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/profiling.json")

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.loki,
    grafana_data_source.tempo,
    grafana_data_source.pyroscope,
  ]
}

# -----------------------------------------------------------------------------
# Organization Preferences
# -----------------------------------------------------------------------------

resource "grafana_organization_preferences" "main" {
  count = var.enable_observability ? 1 : 0

  home_dashboard_uid = "home"

  depends_on = [
    grafana_dashboard.home,
  ]
}
