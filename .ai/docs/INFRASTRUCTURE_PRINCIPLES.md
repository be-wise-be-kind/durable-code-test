# Infrastructure Principles

**Purpose**: Define the core principles and philosophy for infrastructure design

**Scope**: All infrastructure decisions and implementations across all environments

**Overview**: Establishes foundational principles that guide all infrastructure design decisions,
    emphasizing cost optimization, reliability, and maintainability. Defines the architectural
    philosophy for Infrastructure as Code implementation, resource management, security practices,
    and operational excellence that supports scalable and cost-effective deployment strategies.

**Dependencies**: Terraform infrastructure code, AWS services, cost monitoring tools, security frameworks

**Exports**: Infrastructure design principles, architectural guidelines, cost optimization strategies

**Related**: TERRAFORM_STANDARDS.md, AWS deployment documentation, cost management guidelines

**Implementation**: Infrastructure as Code patterns, cost-first design decisions, automated resource management

---

## Infrastructure Philosophy
Core principles and philosophy that guide infrastructure design decisions and implementation strategies.

### Infrastructure as Code
We treat infrastructure as software - versioned, tested, and reproducible. Every resource exists as code, enabling consistent deployments across environments.

### Cost-First Design
Every architectural decision considers cost impact. We optimize for minimal spend while maintaining reliability through:
- Resource right-sizing based on actual needs
- Spot instances for non-critical workloads
- Auto-shutdown for development environments
- Single-AZ deployments where HA isn't critical

### Immutable and Ephemeral
Infrastructure can be destroyed and recreated at will. No manual configuration or "pet" servers. State is external to compute resources.

### Security by Default
- Least privilege IAM policies
- Private subnets for compute
- Security groups as defense in depth
- Secrets in environment variables, never in code

## What We Deploy

### Core Components
- **Networking**: VPC with public/private subnet separation
- **Compute**: ECS Fargate for serverless container execution
- **Load Balancing**: ALB for traffic distribution and SSL termination
- **Storage**: ECR for container images, S3 for static assets
- **DNS**: Route53 for domain management when needed

### Environment Strategy
- **Dev**: Minimal resources, aggressive cost optimization, ephemeral
- **Staging**: Production-like but smaller, used for final validation
- **Production**: Reliable and monitored, but still cost-conscious

## How We Deploy

### Terraform Patterns
- Remote state in S3 with DynamoDB locking
- Environment-specific tfvars files
- Modular but pragmatic - avoid over-abstraction
- Tagged resources for cost tracking

### Deployment Philosophy
- All changes through CI/CD pipeline
- No manual AWS console changes
- Infrastructure changes are reviewed like code
- Rollback strategy for every change

## Cost Optimization Strategies

### Compute
- Fargate Spot for 70% savings in dev/staging
- Minimum viable task sizes (256 CPU / 512 MB)
- Auto-scaling with conservative thresholds

### Networking
- Single NAT Gateway in dev ($45/month → $45/month)
- Cross-zone load balancing disabled
- VPC endpoints only when cost-justified

### Storage
- ECR lifecycle policies to limit image retention
- S3 lifecycle rules for log rotation
- CloudWatch log expiration

### Scheduling
- Auto-shutdown outside business hours (60%+ savings)
- Weekend shutdowns for dev environments
- On-demand wake capability

### Selective Resource Management
- **Preserve Low-Cost, Slow-Provision Resources**:
  - ACM certificates (free, 30+ min validation)
  - Route53 hosted zones ($0.50/month)
  - ECR repositories (pay per GB stored)
  - Target groups and security groups (free)
- **Destroy High-Cost Resources When Idle**:
  - NAT Gateway ($45/month, provisions in seconds)
  - ALB ($18/month, provisions quickly)
  - Running ECS tasks (pay per hour)
  - EIP when unattached ($3.60/month)
- **Smart Shutdown Strategy**:
  - `just infra-down-expensive`: Removes NAT, ALB, ECS services
  - `just infra-up`: Quickly restores from preserved base
  - Total restart time: <5 minutes vs 30+ minutes full rebuild

## Monitoring Philosophy

### What We Monitor
- Service health and availability
- Cost trends and anomalies
- Security events and compliance
- Performance only when it impacts users

### Alert Strategy
- Alert on user impact, not infrastructure metrics
- Escalate based on severity and time
- Automatic remediation where possible

## Disaster Recovery

### Backup Strategy
- Infrastructure can be recreated from code
- Application data backed up separately
- Database snapshots with defined retention

### Recovery Objectives
- RTO: 1 hour for production
- RPO: 1 hour for critical data
- Dev/staging can be recreated on demand

## Technology Choices

### Why Fargate
- No EC2 instance management
- Pay only for actual compute used
- Automatic security patching
- Native container support

### Why ALB
- Layer 7 load balancing
- Native AWS service integration
- SSL termination at load balancer
- Health checking and auto-recovery

### Why Terraform
- Multi-cloud potential
- Mature ecosystem
- Declarative infrastructure
- Strong state management

## Anti-Patterns We Avoid

- Over-engineering for unlikely scenarios
- Multi-region without clear requirements
- High availability when downtime is acceptable
- Expensive services when alternatives exist
- Manual infrastructure changes
- Untagged resources
- Hardcoded secrets or credentials

## Future Considerations

When needs change, we'll evaluate:
- Kubernetes if container orchestration complexity increases
- CloudFront CDN for global distribution
- Aurora Serverless for database needs
- Lambda for event-driven workloads

But we'll adopt only when the value justifies the complexity and cost.
