#!/bin/bash

# Task Remove Script
# Usage: ./task-remove.sh <task_id> [--confirm]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
TASK_ID=""
CONFIRMED=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --confirm)
            CONFIRMED=true
            shift
            ;;
        --help)
            echo "Usage: $0 <task_id> [--confirm]"
            echo ""
            echo "Remove a task from the TaskManager system"
            echo ""
            echo "Arguments:"
            echo "  task_id                   ID of the task to remove"
            echo ""
            echo "Options:"
            echo "  --confirm                 Skip confirmation prompt"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 task_123               # Remove task_123 with confirmation"
            echo "  $0 task_123 --confirm     # Remove task_123 without confirmation"
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
                echo "Multiple task IDs provided. Only one task can be removed at a time."
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

# First get task info and confirm if needed
if [[ "$CONFIRMED" == false ]]; then
    echo "🔍 Getting task information..."
    
    node -e "
    const TaskManager = require('./lib/taskManager');
    const taskManager = new TaskManager('./TODO.json');
    
    taskManager.readTodo()
        .then(todoData => {
            const task = todoData.tasks.find(t => t.id === '$TASK_ID');
            if (!task) {
                throw new Error('Task not found: $TASK_ID');
            }
            
            console.log('📋 Task to be removed:');
            console.log('   ID:', task.id);
            console.log('   Title:', task.title);
            console.log('   Status:', task.status);
            console.log('   Mode:', task.mode || 'DEVELOPMENT');
            
            console.log();
            console.log('⚠️  This action cannot be undone!');
            console.log('Are you sure you want to remove this task? (y/N)');
            process.exit(2); // Special exit code for confirmation
        })
        .catch(error => {
            console.error('❌ Error getting task info:', error.message);
            process.exit(1);
        });
    "
    
    # Handle confirmation
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 2 ]; then
        read -r CONFIRM
        if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
            echo "❌ Operation cancelled"
            exit 1
        fi
        CONFIRMED=true
    elif [ $EXIT_CODE -ne 0 ]; then
        exit $EXIT_CODE
    fi
fi

# Remove the task
echo "🗑️  Removing task..."
echo "   Task ID: $TASK_ID"

node -e "
const TaskManager = require('./lib/taskManager');
const taskManager = new TaskManager('./TODO.json');

taskManager.removeTask('$TASK_ID')
    .then(removed => {
        if (removed) {
            console.log('✅ Task removed successfully!');
            console.log('🗂️  Task has been permanently deleted');
        } else {
            throw new Error('Task not found or could not be removed: $TASK_ID');
        }
    })
    .catch(error => {
        console.error('❌ Error removing task:', error.message);
        process.exit(1);
    });
"