#!/bin/bash

# Task Add File Script
# Usage: ./task-add-file.sh <task_id> <file_path>

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
            echo "Add an important file to a task"
            echo ""
            echo "Arguments:"
            echo "  task_id                   ID of the task to add file to"
            echo "  file_path                 Path to the file to add"
            echo ""
            echo "Options:"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 task_123 src/login.js  # Add src/login.js to task_123"
            echo "  $0 task_456 docs/api.md   # Add docs/api.md to task_456"
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

echo "📎 Adding file to task..."
echo "   Task ID: $TASK_ID"
echo "   File Path: $FILE_PATH"
echo

# Add file to task
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
        
        if (task.important_files && task.important_files.includes('$FILE_PATH')) {
            console.log('ℹ️  File is already associated with this task');
            return false;
        }
        
        console.log('   Current Files:', task.important_files ? task.important_files.length : 0);
        
        // Add the file
        return taskManager.addImportantFile('$TASK_ID', '$FILE_PATH');
    })
    .then(added => {
        if (added === false) {
            // File already exists, not an error
            return;
        }
        
        if (added) {
            console.log('✅ File added successfully!');
            console.log('📎 File is now associated with the task');
            
            // Show updated file list
            return taskManager.readTodo().then(todoData => {
                const task = todoData.tasks.find(t => t.id === '$TASK_ID');
                if (task.important_files && task.important_files.length > 0) {
                    console.log();
                    console.log('📁 All associated files:');
                    task.important_files.forEach((file, index) => {
                        const marker = file === '$FILE_PATH' ? '✨ ' : '   ';
                        console.log(\`\${marker}\${index + 1}. \${file}\`);
                    });
                }
            });
        } else {
            throw new Error('Failed to add file to task');
        }
    })
    .catch(error => {
        console.error('❌ Error adding file to task:', error.message);
        process.exit(1);
    });
"