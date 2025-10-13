# Resource Naming Enforcement - AI Context & Feature Overview

**Purpose**: Comprehensive background and context for AI agents working on resource naming enforcement

**Scope**: Design and implementation context for automated resource naming validation across infrastructure code

**Overview**: Provides AI agents with full context on why resource naming standards matter for AI development,
    how inconsistent naming causes problems, and the solution architecture for automated enforcement. Includes
    project background, current state analysis, target architecture, key decisions, and AI-specific guidance
    for implementing naming validation linters.

**Dependencies**: Design linting framework, infrastructure as code patterns, cloud resource management

**Exports**: Feature context, architectural decisions, implementation guidance

**Related**: PROGRESS_TRACKER.md for current status, PR_BREAKDOWN.md for detailed tasks

**Implementation**: Context-driven feature development with architectural documentation

---

## 🎯 Feature Vision

**Goal**: Ensure AI agents always create consistently named resources that can be easily identified, tracked for costs, and cleaned up automatically.

**Problem Statement**:
Without explicit naming standards, AI creates resources inconsistently across conversations:
- Conversation 1: `my-app-bucket`
- Conversation 2: `app-storage`
- Conversation 3: `storage-main`

This makes it impossible to:
- Find existing resources (AI searches for wrong names)
- Track costs by product or environment
- Identify orphaned resources for cleanup
- Maintain clean infrastructure over time

**Solution**:
Enforce naming pattern `{product}-{env}-{type}-{name}` through automated linting that blocks non-compliant resource names before they enter the codebase.

---

## 📋 Current Application Context

### Existing Infrastructure
- Terraform infrastructure in `infrastructure/` directory
- AWS resources (S3, ECS, ALB, RDS, etc.)
- Multi-environment deployment (dev, staging, prod)
- Product domain: `durableai`

### Current Naming State
**Standards Exist**: `.ai/docs/TERRAFORM_STANDARDS.md` documents the pattern
**Enforcement**: None - AI must remember to follow standards
**Compliance**: Partial - some resources follow pattern, others don't

### Existing Linting Framework
- Custom design linter framework in `tools/design_linters/`
- Multiple rule categories (security, organization, style, solid, testing)
- Integrated into pre-commit hooks
- Can be extended for infrastructure validation

---

## 🏗️ Target Architecture

### Naming Pattern
```
{product-domain}-{environment}-{resource-type}-{specific-name}

Examples:
✅ durableai-prod-assets          (S3 bucket)
✅ durableai-dev-cluster          (ECS cluster)
✅ durableai-staging-alb          (Load balancer)

❌ my-bucket                      (missing product/env)
❌ production-storage             (inconsistent pattern)
❌ app-data                       (too generic)
```

### Required Tags
All resources must have:
- `ProductDomain`: `durableai`
- `Environment`: `dev|staging|prod`
- `ManagedBy`: `terraform`
- `CostCenter`: `engineering`

### Linter Architecture
```
tools/design_linters/rules/infrastructure/naming_rules.py
├── TerraformResourceNamingRule
│   ├── parse_terraform_resources()
│   ├── extract_resource_name()
│   ├── validate_naming_pattern()
│   ├── check_required_tags()
│   └── generate_fix_suggestion()
└── Tests in test/unit_test/tools/design_linters/
```

---

## 🔑 Key Decisions & Tradeoffs

### Decision 1: Universal Pattern vs. Per-Resource Patterns
**Chosen**: Universal pattern `{product}-{env}-{type}`
**Rationale**:
- Simpler for AI to remember one pattern
- Easier to search and filter
- Works across all cloud providers
- Reduces cognitive load

**Alternative Rejected**: Different patterns per resource type
- Would be harder for AI to remember
- More complex to enforce
- Inconsistent search/filtering

### Decision 2: Linter vs. Terraform Module Enforcement
**Chosen**: Linter in design_linters framework
**Rationale**:
- Catches violations before commit
- Works with any IaC tool (not just Terraform)
- Consistent with existing quality gates
- Provides clear error messages

**Alternative Rejected**: Terraform module wrappers
- Only works for Terraform
- Doesn't prevent bad naming in raw resources
- More invasive to existing code

### Decision 3: Block vs. Warn
**Chosen**: Block non-compliant names (error, not warning)
**Rationale**:
- Naming violations accumulate if not enforced
- Impossible to fix retroactively without breaking changes
- AI needs hard constraints, not suggestions

---

## 🤖 AI-Specific Guidance

### Why This Matters for AI
**AI doesn't maintain consistency across conversations.** Each time AI creates a resource:
- It doesn't remember what naming pattern was used before
- It might use different styles (camelCase, snake_case, kebab-case)
- It might include or omit environment/product identifiers inconsistently

**With enforcement**:
- AI reads standards from `.ai/docs/TERRAFORM_STANDARDS.md`
- Linter blocks any deviation
- AI learns the pattern is mandatory
- Consistency maintained automatically

### Common AI Pitfalls
1. **Generic names**: AI creates `storage`, `database`, `api` without context
2. **Inconsistent delimiters**: Mixes `_`, `-`, and no delimiter
3. **Missing environment**: Creates `myapp-bucket` without `dev/prod`
4. **Wrong order**: Creates `dev-durableai-bucket` instead of `durableai-dev-bucket`

### What AI Should Learn
- **Pattern is mandatory**: `{product}-{env}-{type}-{name}`
- **Tags are required**: All 4 tags must be present
- **No creativity**: Follow pattern exactly, no variations
- **Search by pattern**: When looking for existing resources, use the pattern

---

## 🛠️ Implementation Requirements

### Must Have
- Terraform/HCL parsing capability
- Resource name extraction from `bucket =`, `name =` fields
- Pattern validation with regex
- Tag presence validation
- Clear fix suggestions in error messages

### Nice to Have
- Support for CloudFormation naming
- Database naming validation
- API endpoint naming validation
- Auto-fix capability (suggest corrected name)

### Out of Scope (For Now)
- Renaming existing resources (separate effort)
- Resource name reservations
- Cross-cloud standardization
- DNS naming validation

---

## 📊 Success Criteria

### Definition of Done
- [ ] Naming linter implemented in design_linters framework
- [ ] Validates Terraform resource names
- [ ] Checks required tags present
- [ ] Integrated into pre-commit hooks
- [ ] Integrated into CI/CD
- [ ] All existing infrastructure passes linter
- [ ] Documentation updated
- [ ] Tests added and passing

### Acceptance Criteria
**For AI Agents**:
- AI can no longer commit resources with non-compliant names
- Clear error messages guide AI to fix
- AI consistently follows pattern across all conversations

**For Developers**:
- Pre-commit hook catches violations before commit
- CI/CD blocks PRs with naming issues
- Easy to understand what's wrong and how to fix

---

## 🔗 Integration Points

### Existing Systems
- Design linters framework (`tools/design_linters/`)
- Pre-commit hooks (`.pre-commit-config.yaml`)
- CI/CD workflows (`.github/workflows/`)
- Terraform infrastructure (`infrastructure/`)

### Dependencies
- Python 3.11+
- HCL parsing library (python-hcl2 or pyhcl)
- Design linter framework interfaces
- pytest for testing

### Impacted Areas
- All Terraform files will be validated
- Pre-commit will run naming checks
- CI/CD will enforce naming standards
- CLAUDE.md instructions will include naming guidance

---

## 📚 Reference Documentation

### Internal Docs
- `.ai/docs/TERRAFORM_STANDARDS.md` - Current naming standards
- `tools/design_linters/README.md` - Linter framework docs
- `.ai/howto/create-roadmap-item.md` - How this roadmap was created

### External References
- [Terraform Resource Naming Best Practices](https://www.terraform-best-practices.com/naming)
- [AWS Tagging Strategies](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
- [Python HCL2 Parser](https://github.com/amplify-education/python-hcl2)

---

## 💡 Tips for AI Agents

1. **Start with standards review**: Read TERRAFORM_STANDARDS.md thoroughly
2. **Study existing linters**: Look at other rules in `tools/design_linters/rules/`
3. **Test incrementally**: Build parser first, then validation, then integration
4. **Use clear error messages**: AI needs to know exactly what's wrong and how to fix
5. **Document the "why"**: Explain why each rule exists for future AI agents
6. **Think universally**: Pattern should work for any resource type, not just Terraform

---

## 🚀 Next Steps

See **PROGRESS_TRACKER.md** for current status and next PR to implement.
See **PR_BREAKDOWN.md** for detailed implementation instructions.
