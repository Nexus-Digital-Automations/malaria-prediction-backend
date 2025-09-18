#!/bin/bash

# Task Info Script
# Usage: ./task-info.sh <task_id>

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
            echo "Show detailed information about a task"
            echo ""
            echo "Arguments:"
            echo "  task_id                   ID of the task to show info for"
            echo ""
            echo "Options:"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 task_123               # Show info for task_123"
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
                echo "Multiple task IDs provided. Only one task can be shown at a time."
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

# Show task information
node -e "
const TaskManager = require('./lib/taskManager');
const taskManager = new TaskManager('./TODO.json');

taskManager.readTodo()
    .then(todoData => {
        const task = todoData.tasks.find(t => t.id === '$TASK_ID');
        if (!task) {
            throw new Error('Task not found: $TASK_ID');
        }
        
        console.log('📋 Task Information');
        console.log('═'.repeat(50));
        console.log('ID:', task.id);
        console.log('Title:', task.title);
        console.log('Status:', task.status);
        console.log('Mode:', task.mode || 'DEVELOPMENT');
        console.log('Priority:', task.priority || 'medium');
        
        if (task.assigned_agent) {
            console.log('Assigned Agent:', task.assigned_agent);
        }
        
        if (task.created_at) {
            console.log('Created:', new Date(task.created_at).toLocaleString());
        }
        
        if (task.updated_at) {
            console.log('Updated:', new Date(task.updated_at).toLocaleString());
        }
        
        if (task.completed_at) {
            console.log('Completed:', new Date(task.completed_at).toLocaleString());
        }
        
        console.log();
        console.log('Description:');
        console.log('─'.repeat(50));
        console.log(task.description || 'No description provided');
        
        if (task.dependencies && task.dependencies.length > 0) {
            console.log();
            console.log('Dependencies:');
            console.log('─'.repeat(20));
            task.dependencies.forEach(dep => console.log('  -', dep));
        }
        
        if (task.important_files && task.important_files.length > 0) {
            console.log();
            console.log('Important Files:');
            console.log('─'.repeat(20));
            task.important_files.forEach(file => console.log('  -', file));
        }
        
        if (task.quality_gates && task.quality_gates.length > 0) {
            console.log();
            console.log('Quality Gates:');
            console.log('─'.repeat(20));
            task.quality_gates.forEach(gate => console.log('  -', gate));
        }
        
        if (task.errors && task.errors.length > 0) {
            console.log();
            console.log('Errors:');
            console.log('─'.repeat(20));
            task.errors.forEach(error => {
                console.log('  - Type:', error.type);
                console.log('    Message:', error.message);
                console.log('    Blocking:', error.blocking ? 'Yes' : 'No');
                if (error.timestamp) {
                    console.log('    When:', new Date(error.timestamp).toLocaleString());
                }
                console.log();
            });
        }
        
        console.log('═'.repeat(50));
    })
    .catch(error => {
        console.error('❌ Error getting task info:', error.message);
        process.exit(1);
    });
"