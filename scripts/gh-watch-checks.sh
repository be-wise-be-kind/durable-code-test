#!/bin/bash
# Purpose: Real-time dashboard monitoring for GitHub Actions CI/CD checks on pull requests
# Scope: GitHub Actions workflow monitoring and pull request status tracking
# Overview: Interactive terminal dashboard that continuously monitors GitHub Actions check status for pull requests.
#           Auto-detects current PR or accepts PR number as argument, displays real-time check progress with colored status indicators,
#           provides comprehensive summary statistics, and automatically exits when all checks pass successfully.
#           Designed for developer workflow integration during code review and CI/CD monitoring.
# Dependencies: gh (GitHub CLI), jq (JSON processor), bash with color support, active GitHub repository context
# Usage: ./scripts/gh-watch-checks.sh [PR_NUMBER] (auto-detects current PR if number not provided)
# Interfaces: GitHub CLI API calls, JSON processing, and formatted terminal dashboard output
# Implementation: Polling-based monitoring with configurable refresh intervals, ANSI color formatting, and graceful exit handling

set -euo pipefail

# Color definitions
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly RED='\033[0;31m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'  # No Color
readonly CLEAR='\033[2J\033[H'

# Configuration
readonly CHECK_INTERVAL=${GH_CHECK_INTERVAL:-5}
readonly BASE_BRANCH=${GH_BASE_BRANCH:-main}

# Get PR number from argument or detect from current branch
PR_NUMBER="${1:-}"
if [ -z "$PR_NUMBER" ]; then
    PR_NUMBER=$(gh pr view --json number -q .number 2>/dev/null || echo "")
fi

# Validate PR exists
if [ -z "$PR_NUMBER" ]; then
    echo -e "${RED}❌ No PR found for current branch${NC}"
    echo -e "${YELLOW}💡 Create a PR first with: just gh-pr-create${NC}"
    exit 1
fi

# Function to draw dashboard header
draw_header() {
    printf "${CLEAR}"
    printf "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}\n"
    printf "${CYAN}║                   GitHub CI/CD Check Dashboard                  ║${NC}\n"
    printf "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}\n"
    printf "\n"
}

# Function to display PR information
show_pr_info() {
    local pr_info
    pr_info=$(gh pr view "$PR_NUMBER" --json title,number,headRefName,author,state 2>/dev/null)

    if [ $? -eq 0 ]; then
        printf "${BOLD}📋 PR Information:${NC}\n"
        printf "  PR: #%s - %s\n" \
            "$(echo "$pr_info" | jq -r .number)" \
            "$(echo "$pr_info" | jq -r .title)"
        printf "  Branch: %s\n" "$(echo "$pr_info" | jq -r .headRefName)"
        printf "  Author: %s\n" "$(echo "$pr_info" | jq -r .author.login)"
        printf "  State: %s\n" "$(echo "$pr_info" | jq -r .state)"
        printf "\n"
        return 0
    else
        printf "${RED}❌ Failed to fetch PR information${NC}\n"
        return 1
    fi
}

# Function to format check status
format_check_status() {
    local check_data="$1"
    local status conclusion name

    status=$(echo "$check_data" | jq -r .status)
    conclusion=$(echo "$check_data" | jq -r .conclusion)
    name=$(echo "$check_data" | jq -r .name)

    # statusCheckRollup uses uppercase values
    case "$conclusion" in
        SUCCESS)
            printf "${GREEN}✅ ${name} - PASSED${NC}\n"
            ;;
        FAILURE)
            printf "${RED}❌ ${name} - FAILED${NC}\n"
            ;;
        CANCELLED)
            printf "${YELLOW}⚠️  ${name} - CANCELLED${NC}\n"
            ;;
        null|"")
            case "$status" in
                IN_PROGRESS)
                    printf "${BLUE}🔄 ${name} - RUNNING${NC}\n"
                    ;;
                QUEUED)
                    printf "${YELLOW}⏳ ${name} - QUEUED${NC}\n"
                    ;;
                PENDING)
                    printf "${YELLOW}⏳ ${name} - PENDING${NC}\n"
                    ;;
                *)
                    printf "${MAGENTA}❓ ${name} - UNKNOWN${NC}\n"
                    ;;
            esac
            ;;
        *)
            printf "${MAGENTA}❓ ${name} - ${conclusion}${NC}\n"
            ;;
    esac
}

# Function to display checks and summary
show_checks() {
    local checks
    checks=$(gh pr view "$PR_NUMBER" --json statusCheckRollup -q '.statusCheckRollup' 2>/dev/null)

    if [ $? -ne 0 ] || [ "$(echo "$checks" | jq length)" -eq 0 ]; then
        printf "${YELLOW}⏳ Waiting for checks to start...${NC}\n"
        return 1
    fi

    printf "${BOLD}🔄 Check Status:${NC} (Updated: $(date +"%H:%M:%S"))\n"
    printf "────────────────────────────────────────────────────────────────\n"

    # Display each check
    echo "$checks" | jq -c '.[]' | while read -r check; do
        format_check_status "$check"
    done

    printf "\n"

    # Calculate summary (using uppercase values for statusCheckRollup)
    local total passed failed running queued
    total=$(echo "$checks" | jq length)
    passed=$(echo "$checks" | jq '[.[] | select(.conclusion == "SUCCESS")] | length')
    failed=$(echo "$checks" | jq '[.[] | select(.conclusion == "FAILURE")] | length')
    running=$(echo "$checks" | jq '[.[] | select(.status == "IN_PROGRESS")] | length')
    queued=$(echo "$checks" | jq '[.[] | select(.status == "QUEUED" or .status == "PENDING")] | length')

    printf "${BOLD}📊 Summary:${NC}\n"
    printf "  Total: %d | ${GREEN}Passed: %d${NC} | ${RED}Failed: %d${NC} | ${BLUE}Running: %d${NC} | ${YELLOW}Queued: %d${NC}\n" \
        "$total" "$passed" "$failed" "$running" "$queued"
    printf "\n"

    # Status messages
    if [ "$failed" -gt 0 ]; then
        printf "${RED}${BOLD}⚠️  FAILURES DETECTED${NC}\n"
        printf "${YELLOW}Run 'just gh-check-details' for failure logs${NC}\n"
    elif [ "$running" -gt 0 ] || [ "$queued" -gt 0 ]; then
        printf "${BLUE}${BOLD}🔄 Checks in progress...${NC}\n"
    elif [ "$passed" = "$total" ] && [ "$total" -gt 0 ]; then
        printf "${GREEN}${BOLD}✅ All checks passed!${NC}\n"
        printf "${YELLOW}Ready to merge with: just gh-pr-merge${NC}\n"
        return 0
    fi

    return 1
}

# Main dashboard loop
main() {
    echo -e "${CYAN}Starting GitHub Checks Dashboard...${NC}"
    echo -e "${YELLOW}Monitoring PR #${PR_NUMBER}${NC}"
    echo -e "${YELLOW}⏱️  NOTE: GitHub checks may take up to 3 minutes to start${NC}"
    echo ""

    # Trap to restore cursor on exit
    trap 'printf "\033[?25h"' EXIT INT TERM

    while true; do
        clear
        draw_header

        if show_pr_info; then
            if show_checks; then
                # All checks passed - exit successfully
                printf "\n"
                printf "────────────────────────────────────────────────────────────────\n"
                printf "${GREEN}${BOLD}🎉 All checks complete and passing! Exiting dashboard.${NC}\n"
                sleep 2
                exit 0
            fi
        fi

        printf "\n"
        printf "────────────────────────────────────────────────────────────────\n"
        printf "${CYAN}🔄 Auto-refresh: ${CHECK_INTERVAL}s | Press Ctrl+C to exit${NC}\n"

        sleep "$CHECK_INTERVAL"
    done
}

# Run main function
main
