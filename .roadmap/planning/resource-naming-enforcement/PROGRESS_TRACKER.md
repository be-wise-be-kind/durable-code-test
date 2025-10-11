# Resource Naming Enforcement - Progress Tracker & AI Agent Handoff Document

**Purpose**: Primary AI agent handoff document for Resource Naming Enforcement with current progress tracking and implementation guidance

**Scope**: Automated enforcement of resource naming conventions across infrastructure, databases, and cloud resources

**Overview**: Primary handoff document for AI agents working on the Resource Naming Enforcement feature.
    Tracks implementation progress for creating linting rules that enforce consistent resource naming patterns
    across all infrastructure code (Terraform, CloudFormation, etc.). Ensures AI agents always follow
    standardized naming conventions like {product}-{env}-{type}-{name} with required tagging for cost
    tracking, resource identification, and automated cleanup capabilities.

**Dependencies**: Design linting framework, Terraform standards documentation, pre-commit hooks

**Exports**: Progress tracking, implementation guidance, AI agent coordination, and naming enforcement roadmap

**Related**: AI_CONTEXT.md for feature overview, PR_BREAKDOWN.md for detailed tasks

**Implementation**: Progress-driven coordination with systematic validation, checklist management, and AI agent handoff procedures

---

## 🤖 Document Purpose
This is the **PRIMARY HANDOFF DOCUMENT** for AI agents working on the Resource Naming Enforcement feature. When starting work on any PR, the AI agent should:
1. **Read this document FIRST** to understand current progress and feature requirements
2. **Check the "Next PR to Implement" section** for what to do
3. **Reference the linked documents** for detailed instructions
4. **Update this document** after completing each PR

## 📍 Current Status
**Current PR**: Planning Phase - No PRs started
**Infrastructure State**: Naming standards documented in .ai/docs/TERRAFORM_STANDARDS.md but not enforced
**Feature Target**: Automated linting to enforce naming conventions across all infrastructure code

## 📁 Required Documents Location
```
roadmap/planning/resource-naming-enforcement/
├── AI_CONTEXT.md          # Overall feature architecture and context
├── PR_BREAKDOWN.md        # Detailed instructions for each PR
├── PROGRESS_TRACKER.md    # THIS FILE - Current progress and handoff notes
```

## 🎯 Next PR to Implement

### ➡️ START HERE: PR1 - Expand Naming Standards Documentation

**Quick Summary**:
Expand .ai/docs/TERRAFORM_STANDARDS.md to cover all resource types beyond Terraform (database names, service names, API endpoints, etc.). Document naming patterns that apply universally across any infrastructure technology.

**Pre-flight Checklist**:
- [ ] Read existing TERRAFORM_STANDARDS.md to understand current patterns
- [ ] Identify all resource types in codebase that need naming standards
- [ ] Review what naming patterns already exist (good and bad examples)

**Prerequisites Complete**:
- ✅ Naming standards card added to Repository tab
- ✅ Roadmap item created

---

## Overall Progress
**Total Completion**: 0% (0/4 PRs completed)

```
[░░░░░░░░░░░░░░░░░░░░] 0% Complete
```

---

## PR Status Dashboard

| PR | Title | Status | Completion | Complexity | Priority | Notes |
|----|-------|--------|------------|------------|----------|-------|
| PR1 | Expand Naming Standards Documentation | 🔴 Not Started | 0% | Low | Critical | Document all resource types |
| PR2 | Create Custom Naming Linter Rule | 🔴 Not Started | 0% | High | Critical | Terraform/HCL parsing required |
| PR3 | Scan and Fix Non-Compliant Names | 🔴 Not Started | 0% | Medium | Important | Apply standards to existing code |
| PR4 | Integrate into Pre-commit and CI/CD | 🔴 Not Started | 0% | Low | Important | Add to quality gates |

### Status Legend
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Complete
- 🔵 Blocked
- ⚫ Cancelled

---

## PR1: Expand Naming Standards Documentation

### Objective
Document universal naming standards that apply to all resource types, not just Terraform.

### Tasks
- [ ] Review current TERRAFORM_STANDARDS.md naming section
- [ ] Identify all resource types needing standards:
  - [ ] AWS resources (S3, ECS, Lambda, RDS, etc.)
  - [ ] Database schemas and tables
  - [ ] API endpoints
  - [ ] Service names
  - [ ] Environment variables
- [ ] Document naming pattern: `{product}-{env}-{type}-{name}`
- [ ] Provide examples for each resource type
- [ ] Document required tags (ProductDomain, Environment, ManagedBy, CostCenter)
- [ ] Add "why this matters for AI" explanation
- [ ] Create bad examples (what AI does without standards)
- [ ] Create good examples (correct naming)

### Success Criteria
- [ ] All resource types have documented naming patterns
- [ ] Clear examples for each category
- [ ] AI-specific guidance explaining the problem

---

## PR2: Create Custom Naming Linter Rule

### Objective
Build custom linter rule in tools/design_linters/rules/ that validates resource naming.

### Tasks
- [ ] Create `tools/design_linters/rules/infrastructure/naming_rules.py`
- [ ] Implement Terraform/HCL parsing for resource blocks
- [ ] Extract resource names from `bucket = ` and `name = ` assignments
- [ ] Validate pattern: `{product}-{env}-{type}`
- [ ] Check for required tags in resource blocks
- [ ] Report violations with specific fix suggestions
- [ ] Add tests for the linter rule
- [ ] Test against existing infrastructure code
- [ ] Document the rule in design_linters/README.md

### Success Criteria
- [ ] Linter detects non-compliant resource names
- [ ] Provides specific fix suggestions
- [ ] Runs via `make lint-custom`
- [ ] All tests pass

---

## PR3: Scan and Fix Non-Compliant Names

### Objective
Apply naming standards to all existing infrastructure code.

### Tasks
- [ ] Run naming linter against all infrastructure code
- [ ] Identify all non-compliant resources
- [ ] Create migration plan for renaming
- [ ] Update resource names to follow pattern
- [ ] Add missing required tags
- [ ] Update all references to renamed resources
- [ ] Test infrastructure still deploys correctly
- [ ] Document any resources that can't be renamed (and why)

### Success Criteria
- [ ] All infrastructure resources follow naming pattern
- [ ] All required tags present
- [ ] Infrastructure deploys successfully
- [ ] No linting violations

---

## PR4: Integrate into Pre-commit and CI/CD

### Objective
Add naming linter to automated quality gates.

### Tasks
- [ ] Add naming rule to `.pre-commit-config.yaml`
- [ ] Test pre-commit hook blocks non-compliant names
- [ ] Add to CI/CD quality checks
- [ ] Update CLAUDE.md with naming enforcement guidance
- [ ] Document in .ai/howto/ how to fix naming violations
- [ ] Verify all quality gates work end-to-end

### Success Criteria
- [ ] Pre-commit blocks non-compliant names
- [ ] CI/CD fails on naming violations
- [ ] Documentation explains how to fix issues
- [ ] All tests pass

---

## 🚀 Implementation Strategy

### Phase 1: Documentation (PR1)
Establish clear, universal naming standards that go beyond just Terraform.

### Phase 2: Enforcement (PR2)
Build automated linting to catch violations before they enter the codebase.

### Phase 3: Remediation (PR3)
Clean up existing code to comply with standards.

### Phase 4: Integration (PR4)
Make enforcement automatic through pre-commit hooks and CI/CD.

## 📊 Success Metrics

### Technical Metrics
- 100% of infrastructure resources follow naming pattern
- 100% of resources have required tags
- Naming linter integrated into quality gates
- Zero manual intervention needed for enforcement

### Feature Metrics
- AI can successfully find existing resources by name pattern
- Cost tracking works via ProductDomain tag filtering
- Resource cleanup scripts can identify resources by pattern
- AI never creates inconsistently named resources

## 🔄 Update Protocol

After completing each PR:
1. Update PR status in dashboard above
2. Recalculate completion percentage
3. Update "Next PR to Implement" section
4. Document any blockers or deviations
5. Move roadmap item directory if transitioning from 0% → in_progress or → 100%
6. Update master ROADMAP.md with new percentage

---

## 📝 Change Log

| Date | Change | PR |
|------|--------|-----|
| Initial | Created roadmap item | Planning |
