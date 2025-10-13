---
description: Guide for authoring new code following project standards
original_location: .claude/commands/new-code.md
purpose: Comprehensive workflow for code creation and authoring
---

# Code Authoring Guide

This guide outlines the standard workflow for helping users create new code in the project.

## Initial Setup

### 1. Prepare Development Environment
- Ensure you're on the latest code: `git pull origin main`
- Check current branch: `git status`
- If on main branch, create and switch to a feature branch based on the user's requirements
- Branch naming convention: `feat/[description]` or `fix/[description]`

### 2. Gather Requirements
If the user hasn't provided sufficient detail about what they want to create:
- Ask for clarification about the feature or functionality
- Understand the purpose and scope of the new code
- Identify any specific requirements or constraints
- Determine the type of code needed (component, API endpoint, utility, test, etc.)

## Discovery Phase

### 3. Consult Project Index
Start by reading the project index to understand available resources:
- Consult `.ai/index.yaml` for a comprehensive list of:
  - Available templates
  - Feature documentation
  - How-to guides
  - Development standards
  - Existing patterns and examples

### 4. Review Layout Guidelines
Consult `.ai/layout.yaml` to determine proper file placement:
- Review layout rules to understand where different types of files belong
- Identify the appropriate directory structure for the new code
- Verify any placement restrictions or requirements

### 5. Explore Relevant Resources
Based on the index, explore relevant documentation:
- Review applicable feature documentation
- Study related how-to guides
- Examine similar existing code patterns
- Understand integration requirements

## Implementation Phase

### 6. Select Appropriate Templates
Based on the discovery phase, identify and use relevant templates:
- Templates provide standardized starting points
- Adapt templates to specific requirements
- Ensure consistency with project patterns

### 7. Apply Development Standards
Incorporate project standards throughout implementation:
- Follow coding conventions and style guidelines
- Implement proper error handling patterns
- Include appropriate type safety measures
- Add comprehensive documentation

### 8. Create Required Files
Generate the necessary code files:
- Create primary implementation files
- Add corresponding test files when applicable
- Include configuration files if needed
- Update existing files for integration

## Quality Assurance

### 9. Validate Implementation
Ensure the code meets project requirements:
- Run linting and formatting checks
- Execute relevant tests
- Verify integration with existing code
- Confirm adherence to project standards

### 10. Document Changes
Provide appropriate documentation:
- Include inline code documentation
- Add usage examples where helpful
- Update relevant documentation files if needed
- Ensure clear commit messages

## Important Principles

- **Discovery First**: Always explore available resources before creating code
- **Standards Compliance**: Follow established project patterns and conventions
- **User Collaboration**: Engage with the user when requirements need clarification
- **Iterative Refinement**: Be prepared to adjust based on feedback
- **Comprehensive Testing**: Ensure code reliability through appropriate testing

## Workflow Summary

1. Setup environment and branch
2. Clarify requirements if needed
3. Discover available resources through the index
4. Understand layout and placement rules
5. Select and adapt templates
6. Implement with standards
7. Create all necessary files
8. Validate and test
9. Document appropriately
10. Iterate based on feedback

Remember: The goal is to create production-ready code that integrates seamlessly with the existing project structure while maintaining high quality standards.