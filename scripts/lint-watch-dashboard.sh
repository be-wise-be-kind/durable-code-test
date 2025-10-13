#!/bin/bash
# Purpose: Real-time dashboard monitoring for code linting across the project
# Scope: Monitors Python and TypeScript files in app/, tools/, src/, durable-code-app/ directories
# Overview: Interactive terminal dashboard that continuously monitors code quality by running linting checks every 30 seconds.
#           Displays real-time status with visual indicators, statistics, error summaries, and system notifications.
#           Provides a comprehensive overview of linting health with pass/fail rates and detailed error reporting.
# Dependencies: just (for lint-all target), find, wc, grep, bash terminal with color support, optional notification tools (osascript/notify-send/powershell)
# Usage: ./scripts/lint-watch-dashboard.sh (runs in foreground with interactive dashboard)
# Interfaces: Uses 'just lint-all' command and provides visual dashboard with status indicators
# Implementation: Uses ANSI escape codes for terminal control, cursor positioning, and color output with notification system integration

# Dashboard-style file watcher for linting

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Dashboard state
LAST_RUN_TIME="Never"
LAST_STATUS="Waiting"
LAST_FILES=""
LAST_ERRORS=""
TOTAL_RUNS=0
TOTAL_PASSES=0
TOTAL_FAILURES=0
WATCHING_SINCE=$(date +"%H:%M:%S")

# Configuration
CHECK_INTERVAL=30  # Run lint check every 30 seconds
PROJECT_ROOT="/home/stevejackson/Projects/durable-code-test"

# Change to project root
cd "$PROJECT_ROOT"

# Function to clear screen and reset cursor
clear_dashboard() {
    printf '\033[2J\033[H'
}

# Function to move cursor to specific position
move_cursor() {
    printf '\033[%d;%dH' "$1" "$2"
}

# Function to draw a horizontal line
draw_line() {
    printf '%.0s─' {1..80}
    echo
}

# Function to draw the dashboard
draw_dashboard() {
    clear_dashboard

    # Header
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║                         LINT WATCH DASHBOARD                                ║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

    # Status section
    echo
    echo -e "${WHITE}${BOLD}STATUS${NC}"
    draw_line

    # Determine status color and icon
    local status_color="$YELLOW"
    local status_icon="⏳"
    if [ "$LAST_STATUS" = "PASSED" ]; then
        status_color="$GREEN"
        status_icon="✅"
    elif [ "$LAST_STATUS" = "FAILED" ]; then
        status_color="$RED"
        status_icon="❌"
    elif [ "$LAST_STATUS" = "RUNNING" ]; then
        status_color="$BLUE"
        status_icon="🔄"
    fi

    printf "  %-20s ${status_color}%s %s${NC}\n" "Current Status:" "$status_icon" "$LAST_STATUS"
    printf "  %-20s %s\n" "Last Check:" "$LAST_RUN_TIME"
    printf "  %-20s %s\n" "Watching Since:" "$WATCHING_SINCE"

    # Statistics
    echo
    echo -e "${WHITE}${BOLD}STATISTICS${NC}"
    draw_line
    printf "  %-20s %d\n" "Total Runs:" "$TOTAL_RUNS"
    printf "  %-20s ${GREEN}%d${NC} / ${RED}%d${NC}\n" "Pass/Fail:" "$TOTAL_PASSES" "$TOTAL_FAILURES"

    if [ $TOTAL_RUNS -gt 0 ]; then
        local success_rate=$((TOTAL_PASSES * 100 / TOTAL_RUNS))
        local rate_color="$RED"
        [ $success_rate -ge 50 ] && rate_color="$YELLOW"
        [ $success_rate -ge 80 ] && rate_color="$GREEN"
        printf "  %-20s ${rate_color}%d%%${NC}\n" "Success Rate:" "$success_rate"
    fi

    # Scope section
    echo
    echo -e "${WHITE}${BOLD}SCOPE${NC}"
    draw_line
    if [ -n "$LAST_FILES" ]; then
        echo "  ${GRAY}•${NC} $LAST_FILES"
        echo "  ${GRAY}•${NC} Directories: app/, tools/, src/, durable-code-app/"
    else
        echo "  ${GRAY}Waiting for first check...${NC}"
    fi

    # Errors section (only shown if there are errors)
    if [ -n "$LAST_ERRORS" ] && [ "$LAST_STATUS" = "FAILED" ]; then
        echo
        echo -e "${WHITE}${BOLD}LAST ERRORS${NC}"
        draw_line
        echo "$LAST_ERRORS" | head -10 | while IFS= read -r line; do
            [ -n "$line" ] && echo "  $line"
        done
        local error_lines=$(echo "$LAST_ERRORS" | wc -l)
        [ $error_lines -gt 10 ] && echo "  ${GRAY}... and $((error_lines - 10)) more lines${NC}"
    fi

    # Footer
    echo
    draw_line
    echo -e "${GRAY}Press Ctrl+C to stop watching${NC}"
    echo -e "${GRAY}Running 'just lint-all' every 30 seconds...${NC}"
}

# Function to send notifications
send_notification() {
    local title="$1"
    local message="$2"

    # macOS
    if command -v osascript &> /dev/null; then
        osascript -e "display notification \"$message\" with title \"$title\" sound name \"Basso\"" 2>/dev/null
    # Linux
    elif command -v notify-send &> /dev/null; then
        notify-send -u critical "$title" "$message" 2>/dev/null
    # Windows WSL
    elif command -v powershell.exe &> /dev/null; then
        powershell.exe -Command "New-BurntToastNotification -Text '$title', '$message'" 2>/dev/null
    fi
}

# Function to run linting
run_lint() {
    LAST_RUN_TIME=$(date +"%H:%M:%S")
    LAST_STATUS="RUNNING"
    TOTAL_RUNS=$((TOTAL_RUNS + 1))

    # Get list of all Python and TypeScript files
    LAST_FILES=$(find app tools src durable-code-app -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) 2>/dev/null | wc -l)
    LAST_FILES="Checking $LAST_FILES files"

    # Update dashboard to show running status
    draw_dashboard

    # Capture lint output
    lint_output=$(just lint-all 2>&1)
    lint_exit_code=$?

    # Extract only error messages (lines that look like errors)
    LAST_ERRORS=$(echo "$lint_output" | grep -E '(Error|ERROR|Failed|FAILED|✗|error:|ERROR:|violation|Violation)' | head -20)

    if [ $lint_exit_code -eq 0 ]; then
        LAST_STATUS="PASSED"
        TOTAL_PASSES=$((TOTAL_PASSES + 1))
        LAST_ERRORS=""
    else
        LAST_STATUS="FAILED"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
        send_notification "Lint Failed" "Linting errors detected in the codebase"
    fi

    # Redraw dashboard with results
    draw_dashboard
}

# Trap for clean exit
trap 'echo -e "\n${YELLOW}Stopping dashboard...${NC}"; clear_dashboard; exit 0' INT TERM

# Initialize dashboard
draw_dashboard

# Main loop - run lint check every 30 seconds
echo -e "${YELLOW}Running lint check every ${CHECK_INTERVAL} seconds...${NC}"
while true; do
    # Wait for the check interval
    sleep $CHECK_INTERVAL

    # Run the lint check
    run_lint
done
