#!/bin/bash

# Task Complete Script
# Usage: ./task-complete.sh <task_id>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
TASK_ID=""
RUN_LINTER_FEEDBACK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --with-linter)
            RUN_LINTER_FEEDBACK=true
            shift
            ;;
        --help)
            echo "Usage: $0 <task_id> [--with-linter]"
            echo ""
            echo "Mark a task as completed in the TaskManager system"
            echo ""
            echo "Arguments:"
            echo "  task_id                   ID of the task to complete"
            echo ""
            echo "Options:"
            echo "  --with-linter             Run linter feedback immediately on completion"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 task_123               # Mark task_123 as completed"
            echo "  $0 task_123 --with-linter # Mark task_123 as completed and run linter"
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
                echo "Multiple task IDs provided. Only one task can be completed at a time."
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

echo "✅ Marking task as completed..."
echo "   Task ID: $TASK_ID"
if [[ "$RUN_LINTER_FEEDBACK" == "true" ]]; then
    echo "   Linter feedback: Enabled"
fi

# Mark the task as completed
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
        
        // Update task status to completed with optional linter feedback
        const options = $RUN_LINTER_FEEDBACK ? { runLinterFeedback: true } : {};
        return taskManager.updateTaskStatus('$TASK_ID', 'completed', options);
    })
    .then(updated => {
        if (updated) {
            console.log('✅ Task marked as completed successfully!');
            console.log('   Task will be archived to DONE.json');
        } else {
            throw new Error('Failed to update task status');
        }
    })
    .catch(error => {
        console.error('❌ Error completing task:', error.message);
        process.exit(1);
    });
"