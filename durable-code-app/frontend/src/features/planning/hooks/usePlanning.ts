/**
 * Purpose: Custom React hook for managing planning feature data and state
 * Scope: Planning documents, workflows, resources, and case study management
 * Overview: Provides data and utilities for the planning feature components including
 *     project case study tracking for AWS deployment implementation
 * Dependencies: React, planning types
 * Exports: usePlanning custom hook
 * Interfaces: Uses PlanningDocument, PlanningSection, CaseStudyData from types
 * Implementation: Returns planning documents organized by sections and case study data
 */

import { useMemo, useState } from 'react';
import type {
  CaseStudyData,
  CaseStudyStep,
  PlanningDocument,
  PlanningSection,
  UsePlanningReturn,
} from '../types/planning.types';

const PLANNING_DOCUMENTS: PlanningDocument[] = [
  {
    id: 'feature-index',
    icon: '📑',
    title: 'Feature Index',
    description: 'Complete index of all planning documents and artifacts',
    href: '/planning/feature-index.html',
    badge: 'Essential',
    category: 'Essential',
  },
  {
    id: 'metadata',
    icon: '📊',
    title: 'Feature Metadata',
    description: 'Project configuration, team members, and timeline details',
    href: '/planning/metadata.html',
    badge: 'Essential',
    category: 'Essential',
  },
  {
    id: 'progress',
    icon: '📈',
    title: 'Progress Tracking',
    description: 'Current status, weekly updates, and milestone tracking',
    href: '/planning/progress.html',
    badge: 'Active',
    category: 'Active',
  },
  {
    id: 'rollout',
    icon: '🚀',
    title: 'Rollout Plan',
    description: 'Deployment strategy, feature flags, and phased release schedule',
    href: '/planning/rollout-plan.html',
    badge: 'Strategic',
    category: 'Strategic',
  },
  {
    id: 'tech-spec',
    icon: '🔧',
    title: 'Technical Specification',
    description: 'Architecture overview, API endpoints, and integration details',
    href: '/planning/technical-spec.html',
    badge: 'Technical',
    category: 'Technical',
  },
  {
    id: 'testing',
    icon: '✅',
    title: 'Testing Plan',
    description: 'Test scenarios, QA checklist, and validation criteria',
    href: '/planning/testing-plan.html',
    badge: 'Quality',
    category: 'Quality',
  },
  {
    id: 'dev-flow',
    icon: '🔄',
    title: 'Development Flow',
    description:
      'Visual workflow showing the complete development lifecycle with AI integration points',
    href: '/diagrams/durable-code-flow.html?return=Planning',
    badge: 'Visual',
    category: 'Visual',
  },
  {
    id: 'ai-review',
    icon: '📋',
    title: 'AI Review Sequence',
    description: 'Step-by-step sequence diagram for AI code review processes',
    href: '/diagrams/ai-review-sequence.html?return=Planning',
    badge: 'Visual',
    category: 'Visual',
  },
  {
    id: 'implementation',
    icon: '📅',
    title: 'Implementation Plan',
    description: 'Gantt chart showing project timeline and milestones',
    href: '/diagrams/implementation-plan.html?return=Planning',
    badge: 'Timeline',
    category: 'Timeline',
  },
];

const CASE_STUDY_STEPS: CaseStudyStep[] = [
  {
    id: 'step-1-planning',
    stepNumber: 1,
    title: 'Create the Plan',
    icon: '📋',
    subtitle: 'Comprehensive planning phase',
    status: 'completed',
    popup: {
      overview: {
        title: 'Planning Phase Overview',
        points: [
          'Established comprehensive documentation structure',
          'Created 10-PR breakdown for incremental deployment',
          'Defined clear success metrics and timelines',
          'Built interactive architecture diagrams',
          'Set up progress tracking system',
        ],
      },
      documents: {
        title: 'Planning Documents Created',
        items: [
          {
            name: 'AI_CONTEXT.md',
            description: 'Background and context for AI agents',
            purpose: 'Ensures AI understands project goals and constraints',
          },
          {
            name: 'PR_BREAKDOWN.md',
            description: '10 incremental PRs with detailed steps',
            purpose: 'Breaks complex deployment into manageable chunks',
          },
          {
            name: 'PROGRESS_TRACKER.md',
            description: 'Status tracking with checklists',
            purpose: 'Monitors implementation progress and blockers',
          },
          {
            name: 'deployment-flow.html',
            description: 'Interactive deployment architecture diagram',
            purpose: 'Visual guide for team understanding',
          },
        ],
      },
      implementation: {
        title: 'How We Approached Planning',
        points: [
          'Started with cost constraints ($60/month budget)',
          'Chose ECS Fargate for serverless container hosting',
          'Designed for incremental implementation',
          'Created documentation-first approach',
          'Built in rollback strategies from day one',
          'AI-assisted development with strict quality gates',
          'Every AI-generated file passed all checks on first run',
        ],
      },
      outcomes: {
        title: 'Planning Phase Results',
        points: [
          '✅ Clear roadmap established',
          '✅ Team alignment achieved',
          '✅ Risk mitigation identified',
          '✅ Cost estimates validated',
          '✅ Timeline defined (21 days)',
          '🏆 AI-generated code: 0 linting errors, 471 tests passing',
          '🏆 100% compliance with SOLID principles and style guides',
        ],
      },
      links: [
        {
          text: 'View Planning Documents',
          url: '/planning/deployment/',
        },
      ],
    },
  },
  {
    id: 'step-2-aws-setup',
    stepNumber: 2,
    title: 'PR0: Domain & AWS Setup',
    icon: '🌐',
    subtitle: 'AWS account and domain registration',
    status: 'completed',
    popup: {
      overview: {
        title: 'AWS Account & Domain Setup',
        points: [
          'Configure AWS account with billing alerts',
          'Research and select domain name',
          'Set up Terraform backend infrastructure',
          'Create IAM users and permissions',
          'Enable security best practices',
        ],
      },
      documents: {
        title: 'Setup Documentation Created',
        items: [
          {
            name: 'infra/README.md',
            description: 'Comprehensive AWS infrastructure guide',
            purpose: 'Step-by-step setup instructions for team',
          },
          {
            name: 'backend.tf',
            description: 'S3 backend configuration for Terraform state',
            purpose: 'Secure state management with locking',
          },
          {
            name: 'variables.tf',
            description: 'Input variables for all environments',
            purpose: 'Flexible configuration with cost optimization',
          },
          {
            name: 'setup-terraform-backend.sh',
            description: 'Automated backend setup script',
            purpose: 'One-command S3 and DynamoDB creation',
          },
        ],
      },
      implementation: {
        title: 'Completed Implementation (2025-09-23)',
        points: [
          '✅ Created feature branch for PR0',
          '✅ Set up Terraform backend configuration',
          '✅ Created AWS provider and variables',
          '✅ Documented domain recommendations',
          '✅ Created environment-specific configurations',
          '✅ S3 bucket and DynamoDB table for state management',
          '✅ PR0 merged to main - Infrastructure foundation ready',
        ],
      },
      outcomes: {
        title: 'Cost Optimization Strategies',
        points: [
          '💰 Target: < $25/month with auto-shutdown',
          '💰 Fargate Spot for 70% dev savings',
          '💰 Auto-shutdown nights & weekends (66% savings)',
          '💰 Minimal resource sizing (256 CPU/512 Memory)',
          '💰 Domain: ~$12-15/year for .dev TLD',
        ],
      },
      links: [
        {
          text: 'View Infrastructure Code',
          url: 'https://github.com/be-wise-be-kind/durable-code-test/tree/feature/pr0-domain-aws-setup/infra',
        },
      ],
    },
  },
  {
    id: 'step-3-terraform',
    stepNumber: 3,
    title: 'PR1: Terraform Foundation',
    icon: '🏗️',
    subtitle: 'Infrastructure as Code setup',
    status: 'completed',
    popup: {
      overview: {
        title: 'Terraform Foundation Setup',
        points: [
          'Configure AWS provider and backend',
          'Set up S3 state management',
          'Create VPC and networking',
          'Define security groups',
          'Establish tagging strategy',
        ],
      },
      documents: {
        title: 'Infrastructure Files',
        items: [
          {
            name: 'main.tf',
            description: 'Provider and backend configuration',
            purpose: 'Core Terraform setup',
          },
          {
            name: 'networking.tf',
            description: 'VPC, subnets, and routing',
            purpose: 'Network isolation and security',
          },
          {
            name: 'variables.tf',
            description: 'Input variables for flexibility',
            purpose: 'Environment-specific configuration',
          },
        ],
      },
      implementation: {
        title: 'Completed Implementation (2025-09-23)',
        points: [
          '✅ VPC created with CIDR 10.0.0.0/16',
          '✅ Public/private subnets across 2 AZs (us-west-2a, us-west-2b)',
          '✅ Internet Gateway and 2 NAT Gateways deployed',
          '✅ Security groups for ALB and ECS tasks',
          '✅ Route tables and associations configured',
          '⚠️ Cost optimization: Reducing to 1 AZ to save $45/month',
        ],
      },
      outcomes: {
        title: 'Achieved Results',
        points: [
          '✅ Reproducible infrastructure deployed',
          '✅ Version-controlled changes in Git',
          '✅ Multi-environment support (dev/staging/prod)',
          '✅ Secure network foundation established',
          '✅ Cost tracking via comprehensive tags',
          '💰 Initial cost: ~$90/month (2 NAT Gateways)',
          '🎯 Target cost: ~$45/month (optimizing to 1 AZ)',
        ],
      },
    },
  },
  {
    id: 'step-4-ecr',
    stepNumber: 4,
    title: 'PR2: Container Registry',
    icon: '📦',
    subtitle: 'ECR repositories setup',
    status: 'in-progress',
    popup: {
      overview: {
        title: 'ECR Repository Configuration',
        points: [
          'Create repositories for frontend and backend',
          'Enable vulnerability scanning',
          'Set up lifecycle policies',
          'Configure cross-region replication',
          'Establish access policies',
        ],
      },
      documents: {
        title: 'Registry Configuration',
        items: [
          {
            name: 'ecr.tf',
            description: 'Repository definitions',
            purpose: 'Container image storage',
          },
          {
            name: 'lifecycle-policy.json',
            description: 'Image retention rules',
            purpose: 'Cost optimization',
          },
        ],
      },
      implementation: {
        title: 'Key Decisions',
        points: [
          'Keep last 10 production images',
          'Delete untagged after 7 days',
          'Enable scan on push',
          'Use immutable tags',
          'Set up pull-through cache',
        ],
      },
      outcomes: {
        title: 'Benefits Achieved',
        points: [
          '🎯 Automated security scanning',
          '🎯 Cost-controlled storage',
          '🎯 Version history maintained',
          '🎯 Fast image pulls',
          '🎯 Disaster recovery ready',
        ],
      },
    },
  },
  {
    id: 'step-5-ecs',
    stepNumber: 5,
    title: 'PR3: ECS Fargate Setup',
    icon: '🚀',
    subtitle: 'Container orchestration',
    status: 'upcoming',
    popup: {
      overview: {
        title: 'ECS Cluster and Services',
        points: [
          'Create Fargate cluster',
          'Define task definitions',
          'Configure services',
          'Set up service discovery',
          'Enable Container Insights',
        ],
      },
      documents: {
        title: 'ECS Configuration',
        items: [
          {
            name: 'ecs.tf',
            description: 'Cluster and service definitions',
            purpose: 'Container orchestration',
          },
          {
            name: 'task-definitions/',
            description: 'Container specifications',
            purpose: 'Resource allocation and config',
          },
        ],
      },
      implementation: {
        title: 'Service Configuration',
        points: [
          'Frontend: 256 CPU, 512 Memory',
          'Backend: 512 CPU, 1024 Memory',
          'Health checks every 30 seconds',
          'Rolling deployments enabled',
          'Auto-restart on failure',
        ],
      },
      outcomes: {
        title: 'Deployment Capabilities',
        points: [
          '🎯 Zero-downtime deployments',
          '🎯 Automatic scaling ready',
          '🎯 Health monitoring active',
          '🎯 Log aggregation enabled',
          '🎯 Cost-optimized sizing',
        ],
      },
    },
  },
  {
    id: 'step-6-cicd',
    stepNumber: 6,
    title: 'PR5: GitHub Actions CI/CD',
    icon: '⚙️',
    subtitle: 'Automated deployment pipeline',
    status: 'upcoming',
    popup: {
      overview: {
        title: 'CI/CD Pipeline Implementation',
        points: [
          'Configure GitHub OIDC provider',
          'Create deployment workflows',
          'Set up environment secrets',
          'Implement approval gates',
          'Add rollback mechanisms',
        ],
      },
      documents: {
        title: 'Pipeline Configuration',
        items: [
          {
            name: '.github/workflows/deploy.yml',
            description: 'Main deployment workflow',
            purpose: 'Automated deployments',
          },
          {
            name: 'iam.tf',
            description: 'OIDC trust relationship',
            purpose: 'Passwordless authentication',
          },
        ],
      },
      implementation: {
        title: 'Pipeline Features',
        points: [
          'Trigger on push to main',
          'Run tests in parallel',
          'Build and push to ECR',
          'Deploy to ECS',
          'Smoke test validation',
        ],
      },
      outcomes: {
        title: 'Automation Benefits',
        points: [
          '🎯 10-minute deployments',
          '🎯 No manual steps',
          '🎯 Consistent process',
          '🎯 Automatic rollback',
          '🎯 Audit trail complete',
        ],
      },
    },
  },
];

export function usePlanning(): UsePlanningReturn {
  const [loading] = useState(false);
  const [error] = useState<Error | null>(null);

  const planningSection: PlanningSection = useMemo(
    () => ({
      title: 'Planning Documents',
      icon: '📋',
      subtitle:
        'Effective planning is crucial for successful AI-assisted development. Our planning documents provide comprehensive guidance for project setup and execution.',
      documents: PLANNING_DOCUMENTS,
    }),
    [],
  );

  const caseStudy: CaseStudyData = useMemo(
    () => ({
      title: 'AWS Deployment Case Study',
      subtitle:
        'Follow our journey deploying this application to AWS ECS Fargate. Each step documents our planning, implementation, and outcomes.',
      steps: CASE_STUDY_STEPS,
    }),
    [],
  );

  return {
    planningSection,
    caseStudy,
    loading,
    error,
  };
}
