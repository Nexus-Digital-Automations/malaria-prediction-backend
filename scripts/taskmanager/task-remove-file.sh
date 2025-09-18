#!/bin/bash

# Task Remove File Script
# Usage: ./task-remove-file.sh <task_id> <file_path>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
TASK_ID=""
FILE_PATH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            echo "Usage: $0 <task_id> <file_path>"
            echo ""
            echo "Remove an important file from a task"
            echo ""
            echo "Arguments:"
            echo "  task_id                   ID of the task to remove file from"
            echo "  file_path                 Path to the file to remove"
            echo ""
            echo "Options:"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 task_123 src/login.js  # Remove src/login.js from task_123"
            echo "  $0 task_456 docs/api.md   # Remove docs/api.md from task_456"
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
            elif [[ -z "$FILE_PATH" ]]; then
                FILE_PATH="$1"
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

if [[ -z "$FILE_PATH" ]]; then
    echo "Error: file_path is required"
    echo "Use --help for usage information"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

echo "📎 Removing file from task..."
echo "   Task ID: $TASK_ID"
echo "   File Path: $FILE_PATH"
echo

# Remove file from task
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
        
        if (!task.important_files || !task.important_files.includes('$FILE_PATH')) {
            console.log('ℹ️  File is not associated with this task');
            return false;
        }
        
        console.log('   Current Files:', task.important_files.length);
        
        // Remove the file
        return taskManager.removeImportantFile('$TASK_ID', '$FILE_PATH');
    })
    .then(removed => {
        if (removed === false) {
            // File doesn't exist, not an error
            return;
        }
        
        if (removed) {
            console.log('✅ File removed successfully!');
            console.log('📎 File is no longer associated with the task');
            
            // Show updated file list
            return taskManager.readTodo().then(todoData => {
                const task = todoData.tasks.find(t => t.id === '$TASK_ID');
                if (task.important_files && task.important_files.length > 0) {
                    console.log();
                    console.log('📁 Remaining associated files:');
                    task.important_files.forEach((file, index) => {
                        console.log(\`   \${index + 1}. \${file}\`);
                    });
                } else {
                    console.log();
                    console.log('📁 No files associated with this task');
                }
            });
        } else {
            throw new Error('Failed to remove file from task');
        }
    })
    .catch(error => {
        console.error('❌ Error removing file from task:', error.message);
        process.exit(1);
    });
"