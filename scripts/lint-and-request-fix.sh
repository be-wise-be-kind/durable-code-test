#!/bin/bash
# Purpose: Automated linting check for staged files with Claude assistance request
# Scope: Git-staged files validation and developer workflow integration
# Overview: Stages specified files, runs linting checks on staged content, and provides clear feedback to developers.
#           On linting failures, generates detailed instructions for Claude AI to fix the detected issues.
#           Designed for integration into development workflows and pre-commit processes.
# Dependencies: git, just (for lint-all-staged target)
# Usage: ./scripts/lint-and-request-fix.sh [FILE_PATH] (FILE_PATH is optional, stages current file if provided)
# Interfaces: Git staging area operations and just lint-all-staged command
# Implementation: Uses git add for staging, just for linting, and provides structured error reporting with exit codes

# Script to lint staged files and request Claude to fix any issues

cd /home/stevejackson/Projects/durable-code-test

# Stage the file that was just written/edited
git add "$1" 2>/dev/null

# Run linting on staged files
if just lint-all-staged 2>&1; then
    echo "✅ Linting passed - no issues found"
    exit 0
else
    echo "❌ Linting failed - issues detected"
    echo ""
    echo "CLAUDE ACTION REQUIRED: Please fix the linting errors above"
    echo "The following files have linting issues that need to be fixed:"
    git diff --cached --name-only --diff-filter=ACM
    echo ""
    echo "Please:"
    echo "1. Review the linting errors shown above"
    echo "2. Fix each issue in the affected files"
    echo "3. Ensure the code follows project standards"
    exit 1
fi
