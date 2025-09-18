#!/bin/bash

# Task Status Script
# Usage: ./task-status.sh <task_id> <new_status>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
TASK_ID=""
NEW_STATUS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            echo "Usage: $0 <task_id> <new_status>"
            echo ""
            echo "Update the status of a task in the TaskManager system"
            echo ""
            echo "Arguments:"
            echo "  task_id                   ID of the task to update"
            echo "  new_status                New status (pending, in_progress, completed, blocked)"
            echo ""
            echo "Options:"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 task_123 in_progress   # Mark task_123 as in progress"
            echo "  $0 task_456 blocked       # Mark task_456 as blocked"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            if [[ -z "$TASK_ID" ]]; then
                TASK_ID="$1"
            elif [[ -z "$NEW_STATUS" ]]; then
                NEW_STATUS="$1"
            else
                echo "Too many arguments provided."
                echo "Use --help for usage information"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required parameters
if [[ -z "$TASK_ID" ]]; then
    echo "Error: task_id is required"
    echo "Use --help for usage information"
    exit 1
fi

if [[ -z "$NEW_STATUS" ]]; then
    echo "Error: new_status is required"
    echo "Use --help for usage information"
    exit 1
fi

# Validate status
case "$NEW_STATUS" in
    pending|in_progress|completed|blocked)
        # Valid status
        ;;
    *)
        echo "Error: Invalid status '$NEW_STATUS'"
        echo "Valid statuses: pending, in_progress, completed, blocked"
        exit 1
        ;;
esac

# Change to project root
cd "$PROJECT_ROOT"

echo "🔄 Updating task status..."
echo "   Task ID: $TASK_ID"
echo "   New Status: $NEW_STATUS"

# Update task status
node -e "
const TaskManager = require('./lib/taskManager');
const taskManager = new TaskManager('./TODO.json');

// First get the task to show details
taskManager.readTodo()
    .then(todoData => {
        const task = todoData.tasks.find(t => t.id === '$TASK_ID');
        if (!task) {
            throw new Error('Task not found: $TASK_ID');
        }
        
        console.log('📋 Task Details:');
        console.log('   Title:', task.title);
        console.log('   Current Status:', task.status);
        console.log('   ↓');
        console.log('   New Status:', '$NEW_STATUS');
        
        // Update task status
        return taskManager.updateTaskStatus('$TASK_ID', '$NEW_STATUS');
    })
    .then(updated => {
        if (updated) {
            console.log('✅ Task status updated successfully!');
            
            if ('$NEW_STATUS' === 'completed') {
                console.log('📦 Task will be archived to DONE.json');
            }
        } else {
            throw new Error('Failed to update task status');
        }
    })
    .catch(error => {
        console.error('❌ Error updating task status:', error.message);
        process.exit(1);
    });
"