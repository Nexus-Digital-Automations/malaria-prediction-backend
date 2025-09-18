#!/bin/bash

# Task Create Script
# Usage: ./task-create.sh --title "Title" --description "Description" --mode "MODE" [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Initialize variables
TITLE=""
DESCRIPTION=""
MODE="DEVELOPMENT"
PRIORITY="medium"
DEPENDENCIES=""
FILES=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --title)
            TITLE="$2"
            shift 2
            ;;
        --description)
            DESCRIPTION="$2"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --priority)
            PRIORITY="$2"
            shift 2
            ;;
        --dependencies)
            DEPENDENCIES="$2"
            shift 2
            ;;
        --files)
            FILES="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 --title \"Title\" --description \"Description\" --mode \"MODE\" [options]"
            echo ""
            echo "Create a new task in the TaskManager system"
            echo ""
            echo "Required:"
            echo "  --title <title>           Task title"
            echo "  --description <desc>      Task description"
            echo ""
            echo "Optional:"
            echo "  --mode <mode>             Execution mode (DEVELOPMENT, TESTING, etc.)"
            echo "  --priority <priority>     Priority level (low, medium, high, critical)"
            echo "  --dependencies <ids>      Comma-separated task IDs this depends on"
            echo "  --files <paths>           Comma-separated important file paths"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --title \"Fix login bug\" --description \"Users cannot log in with OAuth\""
            echo "  $0 --title \"Add tests\" --description \"Unit tests for auth module\" --mode TESTING"
            echo "  $0 --title \"Deploy\" --description \"Deploy to staging\" --priority high --dependencies task_123,task_456"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$TITLE" ]]; then
    echo "Error: --title is required"
    exit 1
fi

if [[ -z "$DESCRIPTION" ]]; then
    echo "Error: --description is required"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

echo "🔨 Creating new task..."
echo "   Title: $TITLE"
echo "   Mode: $MODE"
echo "   Priority: $PRIORITY"

# Build the task creation command
TASK_CONFIG="{"
TASK_CONFIG="${TASK_CONFIG}\"title\": \"$TITLE\""
TASK_CONFIG="${TASK_CONFIG}, \"description\": \"$DESCRIPTION\""
TASK_CONFIG="${TASK_CONFIG}, \"mode\": \"$MODE\""
TASK_CONFIG="${TASK_CONFIG}, \"priority\": \"$PRIORITY\""
TASK_CONFIG="${TASK_CONFIG}, \"status\": \"pending\""

# Add dependencies if provided
if [[ -n "$DEPENDENCIES" ]]; then
    DEPS_ARRAY="["
    IFS=',' read -ra DEPS <<< "$DEPENDENCIES"
    for i in "${!DEPS[@]}"; do
        DEP="${DEPS[i]// /}"  # Remove spaces
        if [[ $i -gt 0 ]]; then
            DEPS_ARRAY="${DEPS_ARRAY}, "
        fi
        DEPS_ARRAY="${DEPS_ARRAY}\"$DEP\""
    done
    DEPS_ARRAY="${DEPS_ARRAY}]"
    TASK_CONFIG="${TASK_CONFIG}, \"dependencies\": $DEPS_ARRAY"
fi

# Add important files if provided
if [[ -n "$FILES" ]]; then
    FILES_ARRAY="["
    IFS=',' read -ra FILE_LIST <<< "$FILES"
    for i in "${!FILE_LIST[@]}"; do
        FILE="${FILE_LIST[i]// /}"  # Remove spaces
        if [[ $i -gt 0 ]]; then
            FILES_ARRAY="${FILES_ARRAY}, "
        fi
        FILES_ARRAY="${FILES_ARRAY}\"$FILE\""
    done
    FILES_ARRAY="${FILES_ARRAY}]"
    TASK_CONFIG="${TASK_CONFIG}, \"important_files\": $FILES_ARRAY"
fi

TASK_CONFIG="${TASK_CONFIG}}"

# Create the task
RESULT=$(node -e "
const TaskManager = require('./lib/taskManager');
const taskManager = new TaskManager('./TODO.json');

const taskData = $TASK_CONFIG;

taskManager.createTask(taskData)
    .then(taskId => {
        console.log('✅ Task created successfully!');
        console.log('   Task ID:', taskId);
        process.exit(0);
    })
    .catch(error => {
        console.error('❌ Error creating task:', error.message);
        process.exit(1);
    });
")

echo "$RESULT"