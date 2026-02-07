# Purpose: Grafana datasources, folders, dashboards, and organization preferences managed via Terraform provider
# Scope: Grafana API-managed resources for the observability stack, conditional on enable_observability
# Overview: Provisions Grafana datasources, folders, dashboards, and organization preferences using the
#     Grafana Terraform provider instead of file-based provisioning. This approach pushes configuration
#     via the Grafana HTTP API after the EC2 instance and Grafana container are running, avoiding
#     user-data size constraints and ensuring dashboards are deployed to the running instance. Five
#     datasources cover all observability pillars (Mimir, Loki, Tempo, Pyroscope, CloudWatch) with
#     cross-pillar correlation configured. Two Grafana folders (Web, Observability) organize 13
#     dashboards into a drilldown hierarchy loaded from JSON files in
#     infra/observability/grafana/dashboards/. Organization preferences set the home dashboard.
#     All resources depend on the EC2 instance being created. The Grafana provider connects via an
#     SSM port-forward tunnel (localhost:3001), not through the ALB.
# Dependencies: Grafana provider, observability EC2 instance, ALB routing, dashboard JSON files
# Exports: Grafana datasource, folder, and dashboard resources for observability visualization
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
    httpMethod   = "POST"
    timeInterval = "60s"
    exemplarTraceIdDestinations = [
      {
        name          = "traceID"
        datasourceUid = "tempo"
      }
    ]
  })

  depends_on = [
    aws_instance.observability,
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
          value = "service_name"
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
  ]
}

resource "grafana_data_source" "cloudwatch" {
  count = var.enable_observability ? 1 : 0

  type = "cloudwatch"
  name = "CloudWatch"
  uid  = "cloudwatch"

  json_data_encoded = jsonencode({
    defaultRegion = var.aws_region
    authType      = "ec2_iam_role"
  })

  depends_on = [
    aws_instance.observability,
  ]
}

# -----------------------------------------------------------------------------
# Dashboards
# -----------------------------------------------------------------------------

locals {
  dashboard_path = "${path.module}/../../../observability/grafana/dashboards"
}

# -----------------------------------------------------------------------------
# Folders
# -----------------------------------------------------------------------------

resource "grafana_folder" "web" {
  count = var.enable_observability ? 1 : 0

  title = "Web"
  uid   = "web"

  depends_on = [aws_instance.observability]
}

resource "grafana_folder" "observability" {
  count = var.enable_observability ? 1 : 0

  title = "Observability"
  uid   = "observability"

  depends_on = [aws_instance.observability]
}

# -----------------------------------------------------------------------------
# Home Dashboard (root, no folder)
# -----------------------------------------------------------------------------

resource "grafana_dashboard" "home" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/home.json")

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.cloudwatch,
  ]
}

# -----------------------------------------------------------------------------
# Web Dashboards
# -----------------------------------------------------------------------------

resource "grafana_dashboard" "web_summary" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/web-summary.json")
  folder      = grafana_folder.web[0].id

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.cloudwatch,
  ]
}

resource "grafana_dashboard" "web_latency" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/web-latency.json")
  folder      = grafana_folder.web[0].id

  depends_on = [grafana_data_source.mimir]
}

resource "grafana_dashboard" "web_errors" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/web-errors.json")
  folder      = grafana_folder.web[0].id

  depends_on = [grafana_data_source.mimir]
}

resource "grafana_dashboard" "web_traffic" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/web-traffic.json")
  folder      = grafana_folder.web[0].id

  depends_on = [grafana_data_source.mimir]
}

resource "grafana_dashboard" "web_saturation" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/web-saturation.json")
  folder      = grafana_folder.web[0].id

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.cloudwatch,
  ]
}

resource "grafana_dashboard" "web_traces" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/web-traces.json")
  folder      = grafana_folder.web[0].id

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.tempo,
  ]
}

resource "grafana_dashboard" "web_red" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/web-red.json")
  folder      = grafana_folder.web[0].id

  depends_on = [
    grafana_data_source.mimir,
    grafana_data_source.tempo,
  ]
}

resource "grafana_dashboard" "web_frontend" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/web-frontend.json")
  folder      = grafana_folder.web[0].id

  depends_on = [grafana_data_source.loki]
}

# -----------------------------------------------------------------------------
# Observability Dashboards
# -----------------------------------------------------------------------------

resource "grafana_dashboard" "obs_summary" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/obs-summary.json")
  folder      = grafana_folder.observability[0].id

  depends_on = [grafana_data_source.mimir]
}

resource "grafana_dashboard" "obs_saturation" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/obs-saturation.json")
  folder      = grafana_folder.observability[0].id

  depends_on = [grafana_data_source.mimir]
}

resource "grafana_dashboard" "obs_use" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/obs-use.json")
  folder      = grafana_folder.observability[0].id

  depends_on = [grafana_data_source.mimir]
}

resource "grafana_dashboard" "obs_profiling" {
  count = var.enable_observability ? 1 : 0

  config_json = file("${local.dashboard_path}/obs-profiling.json")
  folder      = grafana_folder.observability[0].id

  depends_on = [
    grafana_data_source.pyroscope,
    grafana_data_source.tempo,
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
