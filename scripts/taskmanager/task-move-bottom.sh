#!/bin/bash

# Task Move Bottom Script
# Usage: ./task-move-bottom.sh <task_id>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
TASK_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            echo "Usage: $0 <task_id>"
            echo ""
            echo "Move a task to the bottom priority position"
            echo ""
            echo "Arguments:"
            echo "  task_id                   ID of the task to move to bottom"
            echo ""
            echo "Options:"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 task_123               # Move task_123 to bottom priority"
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
            else
                echo "Multiple task IDs provided. Only one task can be moved at a time."
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

# Change to project root
cd "$PROJECT_ROOT"

echo "⬇️ Moving task to bottom priority..."
echo "   Task ID: $TASK_ID"

# Move task to bottom
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
        
        console.log('📋 Moving task:');
        console.log('   Title:', task.title);
        
        // Move to bottom
        return taskManager.moveTaskToBottom('$TASK_ID');
    })
    .then(moved => {
        if (moved) {
            console.log('✅ Task moved to bottom priority successfully!');
            console.log('🔽 Task is now at the last position');
        } else {
            throw new Error('Failed to move task to bottom');
        }
    })
    .catch(error => {
        console.error('❌ Error moving task:', error.message);
        process.exit(1);
    });
"