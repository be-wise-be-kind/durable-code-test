# Resource Naming Enforcement - PR Breakdown

**Purpose**: Detailed implementation steps for each PR in the naming enforcement roadmap

**Scope**: Step-by-step instructions for implementing resource naming validation linters

**Overview**: Provides specific implementation guidance for each PR including files to create/modify,
    code examples, testing requirements, and success criteria. Breaks down the naming enforcement feature
    into manageable PRs that build incrementally toward automated validation of resource naming patterns.

**Dependencies**: AI_CONTEXT.md for feature overview, PROGRESS_TRACKER.md for current status

**Exports**: Detailed PR implementation instructions, code examples, testing strategies

**Related**: Design linting framework, Terraform standards documentation

**Implementation**: Step-by-step PR breakdowns with specific file paths and code examples

---

## PR1: Expand Naming Standards Documentation

### Goal
Document universal naming standards beyond just Terraform resources.

### Files to Modify
- `.ai/docs/TERRAFORM_STANDARDS.md` (expand to cover all resource types)

### Implementation Steps

#### Step 1: Review Current Standards
Read `.ai/docs/TERRAFORM_STANDARDS.md` lines 34-76 to understand existing pattern.

#### Step 2: Add Universal Resource Types Section
After the existing "Resource Names" section, add:

```markdown
### Universal Resource Naming

The naming pattern `{product-domain}-{environment}-{resource-type}` applies to ALL resources:

#### Infrastructure Resources
- **S3 Buckets**: `durableai-prod-assets`, `durableai-dev-logs`
- **ECS Clusters**: `durableai-prod-cluster`, `durableai-staging-cluster`
- **Load Balancers**: `durableai-prod-alb`, `durableai-dev-nlb`
- **RDS Instances**: `durableai-prod-postgres`, `durableai-dev-mysql`
- **Lambda Functions**: `durableai-prod-api-handler`, `durableai-dev-worker`

#### Database Resources
- **Schemas**: `durableai_prod`, `durableai_dev`
- **Tables**: `durableai_users`, `durableai_sessions`
- **Indexes**: `durableai_users_email_idx`

#### Application Resources
- **Service Names**: `durableai-prod-api`, `durableai-dev-frontend`
- **Queue Names**: `durableai-prod-jobs`, `durableai-dev-notifications`
- **Cache Keys**: `durableai:prod:user:{id}`, `durableai:dev:session:{token}`

### Why This Matters for AI

**Without naming standards**, AI creates resources inconsistently:
```terraform
# Conversation 1
resource "aws_s3_bucket" "storage" {
  bucket = "my-app-bucket"
}

# Conversation 2
resource "aws_s3_bucket" "assets" {
  bucket = "app-storage-prod"
}

# Conversation 3
resource "aws_s3_bucket" "data" {
  bucket = "production-data"
}
```

**Result**: AI cannot find existing resources because it searches for wrong names.

**With naming standards**, AI creates resources consistently:
```terraform
resource "aws_s3_bucket" "assets" {
  bucket = "durableai-${var.environment}-assets"
}
```

**Result**: AI can reliably search for `durableai-*-assets` to find existing buckets.
```

#### Step 3: Add Cost Tracking Section
```markdown
### Cost Tracking Benefits

With consistent naming and tagging:
- **By Product**: `aws ce get-cost-and-usage --filter '{"Tags":{"Key":"ProductDomain","Values":["durableai"]}}'`
- **By Environment**: `aws s3 ls | grep durableai-dev` shows all dev resources
- **By Resource Type**: `aws s3 ls | grep assets` finds all asset buckets
- **Orphan Detection**: Resources NOT matching `durableai-*` pattern are orphans
```

### Testing
- [ ] Documentation accurately reflects pattern
- [ ] Examples cover all major resource types
- [ ] "Why AI" explanation is clear
- [ ] Good and bad examples provided

### Success Criteria
- [ ] All resource types have naming patterns
- [ ] Clear AI-specific guidance
- [ ] Cost tracking benefits explained
- [ ] Ready for linter implementation

---

## PR2: Create Custom Naming Linter Rule

### Goal
Build automated linter to validate resource naming patterns.

### Files to Create
- `tools/design_linters/rules/infrastructure/naming_rules.py`
- `tools/design_linters/rules/infrastructure/__init__.py`
- `test/unit_test/tools/design_linters/test_naming_rules.py`

### Implementation Steps

#### Step 1: Create Infrastructure Rules Directory
```bash
mkdir -p tools/design_linters/rules/infrastructure
touch tools/design_linters/rules/infrastructure/__init__.py
```

#### Step 2: Implement Naming Rule
File: `tools/design_linters/rules/infrastructure/naming_rules.py`

```python
"""
Purpose: Validate resource naming conventions in infrastructure code
Scope: Terraform HCL files with resource definitions
Overview: Custom linting rule that validates infrastructure resource names follow
    the pattern {product}-{env}-{type} and have required tags. Parses Terraform
    HCL files to extract resource blocks and validates naming compliance.
Dependencies: hcl2 parser, design linter framework
Exports: TerraformResourceNamingRule class
Implementation: HCL parsing with pattern validation and tag checking
"""

import re
from pathlib import Path
from typing import List, Optional
try:
    import hcl2
except ImportError:
    hcl2 = None

from tools.design_linters.framework.interfaces import LinterRule, LintViolation, LintContext


class TerraformResourceNamingRule(LinterRule):
    """Validates Terraform resource names follow naming conventions."""

    def __init__(self):
        super().__init__()
        self.rule_id = "infrastructure.naming.terraform-resources"
        self.category = "infrastructure"
        self.severity = "error"
        self.message = "Resource names must follow pattern: {product}-{env}-{type}"

        # Expected pattern: {product}-{environment}-{resource-type}
        self.naming_pattern = re.compile(r'^[a-z][a-z0-9]*-(?:dev|staging|prod|test)-[a-z][a-z0-9\-]*$')

        self.required_tags = {"ProductDomain", "Environment", "ManagedBy", "CostCenter"}

    def should_check_file(self, file_path: Path) -> bool:
        """Only check Terraform files."""
        return file_path.suffix == '.tf'

    def check_file(self, file_path: Path, content: str) -> List[LintViolation]:
        """Parse Terraform file and validate resource naming."""
        if hcl2 is None:
            return []  # Skip if hcl2 not available

        violations = []

        try:
            # Parse Terraform HCL
            tf_dict = hcl2.loads(content)

            # Check resource blocks
            if 'resource' in tf_dict:
                for resource_block in tf_dict['resource']:
                    violations.extend(self._check_resource_block(resource_block, file_path))

        except Exception as e:
            # Don't fail on parse errors, just skip
            pass

        return violations

    def _check_resource_block(self, resource_block: dict, file_path: Path) -> List[LintViolation]:
        """Validate a single resource block."""
        violations = []

        for resource_type, resources in resource_block.items():
            for resource_name, resource_config in resources.items():
                # Extract the actual resource name from config
                actual_name = self._extract_resource_name(resource_config)

                if actual_name:
                    # Check naming pattern
                    if not self._validates_naming_pattern(actual_name):
                        violations.append(LintViolation(
                            rule_id=self.rule_id,
                            file_path=str(file_path),
                            line=self._find_line_number(resource_config),
                            message=f"Resource name '{actual_name}' does not follow pattern: {{product}}-{{env}}-{{type}}",
                            severity=self.severity,
                            suggestion=self._generate_fix_suggestion(actual_name, resource_type)
                        ))

                    # Check required tags
                    missing_tags = self._check_required_tags(resource_config)
                    if missing_tags:
                        violations.append(LintViolation(
                            rule_id=f"{self.rule_id}.tags",
                            file_path=str(file_path),
                            line=self._find_line_number(resource_config),
                            message=f"Resource missing required tags: {', '.join(missing_tags)}",
                            severity=self.severity,
                            suggestion=f"Add tags block with: {', '.join(missing_tags)}"
                        ))

        return violations

    def _extract_resource_name(self, resource_config: dict) -> Optional[str]:
        """Extract resource name from config."""
        # Common name fields in Terraform resources
        name_fields = ['bucket', 'name', 'function_name', 'cluster_name', 'db_name']

        for field in name_fields:
            if field in resource_config:
                value = resource_config[field]
                # Handle variable interpolation (skip validation if using vars)
                if isinstance(value, str) and '${var.' not in value and '${' not in value:
                    return value

        return None

    def _validates_naming_pattern(self, name: str) -> bool:
        """Check if name matches expected pattern."""
        return bool(self.naming_pattern.match(name))

    def _check_required_tags(self, resource_config: dict) -> set:
        """Check which required tags are missing."""
        if 'tags' not in resource_config:
            return self.required_tags

        existing_tags = set(resource_config['tags'].keys())
        return self.required_tags - existing_tags

    def _generate_fix_suggestion(self, current_name: str, resource_type: str) -> str:
        """Generate suggestion for fixing the name."""
        # Extract resource type suffix from Terraform type
        type_suffix = resource_type.split('_')[-1]
        return f"Use pattern: durableai-{{env}}-{type_suffix} (e.g., durableai-prod-{type_suffix})"

    def _find_line_number(self, config: dict) -> int:
        """Extract line number from HCL config (if available)."""
        # HCL2 parser doesn't always provide line numbers
        return 1  # Default to line 1 if not available


# Register rule
def get_rules() -> List[LinterRule]:
    """Return all infrastructure naming rules."""
    return [TerraformResourceNamingRule()]
```

#### Step 3: Add Tests
File: `test/unit_test/tools/design_linters/test_naming_rules.py`

```python
"""
Purpose: Test suite for infrastructure naming validation rules
Scope: Unit tests for Terraform resource naming linter
Overview: Validates that naming linter correctly identifies non-compliant resource
    names and missing tags in Terraform configurations.
Dependencies: pytest, naming_rules module
Exports: Test cases for naming validation
Implementation: Parameterized tests with good and bad examples
"""

import pytest
from pathlib import Path
from tools.design_linters.rules.infrastructure.naming_rules import TerraformResourceNamingRule


class TestTerraformResourceNamingRule:
    """Test Terraform resource naming validation."""

    def test_valid_s3_bucket_name(self):
        """Valid bucket name should pass."""
        rule = TerraformResourceNamingRule()
        content = '''
resource "aws_s3_bucket" "main" {
  bucket = "durableai-prod-assets"

  tags = {
    ProductDomain = "durableai"
    Environment   = "prod"
    ManagedBy     = "terraform"
    CostCenter    = "engineering"
  }
}
'''
        violations = rule.check_file(Path("test.tf"), content)
        assert len(violations) == 0

    def test_invalid_bucket_name_pattern(self):
        """Invalid bucket name should fail."""
        rule = TerraformResourceNamingRule()
        content = '''
resource "aws_s3_bucket" "main" {
  bucket = "my-bucket"

  tags = {
    ProductDomain = "durableai"
    Environment   = "prod"
    ManagedBy     = "terraform"
    CostCenter    = "engineering"
  }
}
'''
        violations = rule.check_file(Path("test.tf"), content)
        assert len(violations) > 0
        assert "does not follow pattern" in violations[0].message

    def test_missing_tags(self):
        """Missing required tags should fail."""
        rule = TerraformResourceNamingRule()
        content = '''
resource "aws_s3_bucket" "main" {
  bucket = "durableai-prod-assets"

  tags = {
    Environment = "prod"
  }
}
'''
        violations = rule.check_file(Path("test.tf"), content)
        assert len(violations) > 0
        assert "missing required tags" in violations[0].message

    def test_skips_variable_interpolation(self):
        """Should skip validation when using variables."""
        rule = TerraformResourceNamingRule()
        content = '''
resource "aws_s3_bucket" "main" {
  bucket = "durableai-${var.environment}-assets"
}
'''
        violations = rule.check_file(Path("test.tf"), content)
        # Should not flag variable interpolation as error
        naming_violations = [v for v in violations if "does not follow pattern" in v.message]
        assert len(naming_violations) == 0
```

#### Step 4: Install HCL Parser
Add to project dependencies (or document in README):
```bash
pip install python-hcl2
# or add to pyproject.toml/requirements.txt
```

#### Step 5: Register Rule with Framework
Add to `tools/design_linters/framework/rule_registry.py` (or equivalent):
```python
from tools.design_linters.rules.infrastructure.naming_rules import get_rules as get_naming_rules

# Register infrastructure rules
infrastructure_rules = get_naming_rules()
```

### Testing
```bash
# Run linter tests
PYTHONPATH=tools python -m pytest test/unit_test/tools/design_linters/test_naming_rules.py -v

# Test against actual infrastructure
PYTHONPATH=tools python -m design_linters.cli --rules infrastructure.naming --format text infrastructure/
```

### Success Criteria
- [ ] Linter detects non-compliant names
- [ ] Validates required tags present
- [ ] Provides clear error messages
- [ ] All tests pass
- [ ] Works on actual Terraform files

---

## PR3: Scan and Fix Non-Compliant Names

### Goal
Apply naming standards to all existing infrastructure code.

### Implementation Steps

#### Step 1: Run Naming Linter
```bash
PYTHONPATH=tools python -m design_linters.cli \
  --rules infrastructure.naming \
  --format text \
  --recursive \
  infrastructure/ > naming-violations.txt
```

#### Step 2: Analyze Violations
Review `naming-violations.txt` and categorize:
- Resources that can be renamed easily
- Resources that require careful migration (databases, S3 buckets with data)
- Resources that can't be renamed (would break production)

#### Step 3: Fix Easy Renames
For resources without data dependencies:
```terraform
# Before
resource "aws_ecs_cluster" "main" {
  name = "my-cluster"
}

# After
resource "aws_ecs_cluster" "main" {
  name = "durableai-${var.environment}-cluster"
}
```

#### Step 4: Document Can't-Rename Items
For resources that can't be renamed, add comments:
```terraform
# Legacy resource - cannot rename without data migration
# TODO: Plan migration to durableai-prod-legacy-data
resource "aws_s3_bucket" "old_bucket" {
  bucket = "my-old-bucket-name"

  tags = {
    ProductDomain = "durableai"
    Environment   = "prod"
    ManagedBy     = "terraform"
    CostCenter    = "engineering"
    Legacy        = "true"  # Exempt from naming standard
  }
}
```

#### Step 5: Add Missing Tags
Update all resources to include required tags:
```terraform
resource "aws_s3_bucket" "assets" {
  bucket = "durableai-${var.environment}-assets"

  tags = {
    ProductDomain = "durableai"
    Environment   = var.environment
    ManagedBy     = "terraform"
    CostCenter    = "engineering"
  }
}
```

### Testing
```bash
# Verify infrastructure still valid
cd infrastructure
terraform init
terraform plan

# Verify no naming violations (except documented legacy)
PYTHONPATH=tools python -m design_linters.cli --rules infrastructure.naming infrastructure/
```

### Success Criteria
- [ ] All renameable resources follow pattern
- [ ] All resources have required tags
- [ ] Legacy resources documented with explanation
- [ ] Terraform plan succeeds
- [ ] No unexpected linting violations

---

## PR4: Integrate into Pre-commit and CI/CD

### Goal
Make naming enforcement automatic.

### Implementation Steps

#### Step 1: Add to Pre-commit Config
File: `.pre-commit-config.yaml`

Add hook:
```yaml
  - repo: local
    hooks:
      - id: infrastructure-naming
        name: Infrastructure Resource Naming
        entry: make lint-infrastructure-naming
        language: system
        files: \\.tf$
        always_run: false
```

#### Step 2: Create Make Target
File: `Makefile.lint` (or main Makefile)

```makefile
.PHONY: lint-infrastructure-naming
lint-infrastructure-naming:
	@echo "Validating infrastructure resource naming..."
	docker exec durable-code-backend \
		python -m design_linters.cli \
		--rules infrastructure.naming \
		--format text \
		--fail-on-error \
		infrastructure/
	@echo "✅ Infrastructure naming validated"
```

#### Step 3: Add to CI/CD
File: `.github/workflows/quality-checks.yml`

Add step to Terraform validation job:
```yaml
      - name: Validate Resource Naming
        run: |
          make lint-infrastructure-naming
```

#### Step 4: Update CLAUDE.md
File: `CLAUDE.md`

Add guidance:
```markdown
## Infrastructure Naming Standards
- All resources must follow pattern: {product}-{env}-{type}-{name}
- Example: durableai-prod-assets, durableai-dev-cluster
- Required tags: ProductDomain, Environment, ManagedBy, CostCenter
- Naming linter will block non-compliant names
- See .ai/docs/TERRAFORM_STANDARDS.md for details
```

#### Step 5: Create How-To Guide
File: `.ai/howto/fix-naming-violations.md`

```markdown
# How to Fix Infrastructure Naming Violations

## When You See This Error
```
infrastructure/main.tf:10: Resource name 'my-bucket' does not follow pattern: {product}-{env}-{type}
```

## Fix Steps

1. **Identify the resource type** from the error message
2. **Update the name** to follow pattern: `durableai-{env}-{type}`
3. **Add required tags** if missing:
   ```terraform
   tags = {
     ProductDomain = "durableai"
     Environment   = var.environment
     ManagedBy     = "terraform"
     CostCenter    = "engineering"
   }
   ```
4. **Verify fix** by running: `make lint-infrastructure-naming`

## Examples

### S3 Bucket
```terraform
# ❌ Before
resource "aws_s3_bucket" "storage" {
  bucket = "my-app-storage"
}

# ✅ After
resource "aws_s3_bucket" "storage" {
  bucket = "durableai-${var.environment}-storage"

  tags = {
    ProductDomain = "durableai"
    Environment   = var.environment
    ManagedBy     = "terraform"
    CostCenter    = "engineering"
  }
}
```
```

### Testing
```bash
# Test pre-commit hook
git add infrastructure/test.tf
git commit -m "test: naming validation"
# Should run naming linter automatically

# Test make target
make lint-infrastructure-naming

# Test CI/CD (push to branch and verify checks run)
git push origin feat/naming-enforcement
```

### Success Criteria
- [ ] Pre-commit hook blocks bad names
- [ ] Make target validates naming
- [ ] CI/CD fails on violations
- [ ] CLAUDE.md documents standards
- [ ] How-to guide explains fixes
- [ ] All quality gates working

---

## 🎯 Overall Success Criteria

After all PRs complete:
- ✅ Naming standards documented for all resource types
- ✅ Linter validates Terraform resource naming
- ✅ All infrastructure code compliant (or documented legacy)
- ✅ Pre-commit blocks non-compliant names
- ✅ CI/CD enforces naming standards
- ✅ Documentation explains how to fix violations
- ✅ AI agents can reliably find resources by name pattern

---

## 📚 References

- Design linter framework: `tools/design_linters/README.md`
- Terraform standards: `.ai/docs/TERRAFORM_STANDARDS.md`
- Pre-commit config: `.pre-commit-config.yaml`
- How to create linters: Look at existing rules in `tools/design_linters/rules/`
