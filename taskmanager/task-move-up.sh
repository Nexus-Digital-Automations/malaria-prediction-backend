#!/bin/bash

# Task Move Up Script
# Usage: ./task-move-up.sh <task_id>

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
            echo "Move a task up one position in priority"
            echo ""
            echo "Arguments:"
            echo "  task_id                   ID of the task to move up"
            echo ""
            echo "Options:"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 task_123               # Move task_123 up one position"
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

echo "⬆️ Moving task up one position..."
echo "   Task ID: $TASK_ID"

# Move task up
node -e "
const TaskManager = require('./lib/taskManager');
const taskManager = new TaskManager('./TODO.json');

// First get the task and its current position
taskManager.readTodo()
    .then(todoData => {
        const taskIndex = todoData.tasks.findIndex(t => t.id === '$TASK_ID');
        if (taskIndex === -1) {
            throw new Error('Task not found: $TASK_ID');
        }
        
        const task = todoData.tasks[taskIndex];
        console.log('📋 Moving task:');
        console.log('   Title:', task.title);
        console.log('   Current Position:', taskIndex + 1);
        
        if (taskIndex === 0) {
            console.log('ℹ️  Task is already at the top position');
            return false;
        }
        
        console.log('   New Position:', taskIndex);
        
        // Move up one position
        return taskManager.moveTaskUp('$TASK_ID');
    })
    .then(moved => {
        if (moved === false) {
            // Already at top, not an error
            return;
        }
        
        if (moved) {
            console.log('✅ Task moved up successfully!');
            console.log('⬆️ Task moved up one position');
        } else {
            throw new Error('Failed to move task up');
        }
    })
    .catch(error => {
        console.error('❌ Error moving task:', error.message);
        process.exit(1);
    });
"