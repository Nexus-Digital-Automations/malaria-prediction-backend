#!/bin/bash

# Current Task Script
# Usage: ./current-task.sh [agent_id]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
AGENT_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            echo "Usage: $0 [agent_id]"
            echo ""
            echo "Get the current active task for an agent or the first pending task"
            echo ""
            echo "Arguments:"
            echo "  agent_id                  Optional agent ID to get current task for"
            echo ""
            echo "Options:"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                        # Get first pending task"
            echo "  $0 agent_1                # Get current task for agent_1"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            if [[ -z "$AGENT_ID" ]]; then
                AGENT_ID="$1"
            else
                echo "Multiple agent IDs provided. Use --help for usage."
                exit 1
            fi
            shift
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

# Call TaskManager to get current task
if [[ -n "$AGENT_ID" ]]; then
    # Get current task for specific agent
    node -e "
    const TaskManager = require('./lib/taskManager');
    const taskManager = new TaskManager('./TODO.json');
    
    taskManager.getCurrentTask('$AGENT_ID')
        .then(task => {
            if (task) {
                console.log('📋 Current Task for $AGENT_ID:');
                console.log('   ID:', task.id);
                console.log('   Title:', task.title);
                console.log('   Status:', task.status);
                console.log('   Mode:', task.mode || 'DEVELOPMENT');
                if (task.assigned_agent) {
                    console.log('   Assigned Agent:', task.assigned_agent);
                }
                console.log();
                console.log('Description:');
                console.log(task.description || 'No description provided');
            } else {
                console.log('📭 No current task assigned to agent $AGENT_ID');
            }
        })
        .catch(error => {
            console.error('❌ Error getting current task:', error.message);
            process.exit(1);
        });
    "
else
    # Get first pending task
    node -e "
    const TaskManager = require('./lib/taskManager');
    const taskManager = new TaskManager('./TODO.json');
    
    taskManager.readTodo()
        .then(todoData => {
            const pendingTasks = todoData.tasks.filter(t => t.status === 'pending');
            
            if (pendingTasks.length > 0) {
                const task = pendingTasks[0];
                console.log('📋 Next Pending Task:');
                console.log('   ID:', task.id);
                console.log('   Title:', task.title);
                console.log('   Status:', task.status);
                console.log('   Mode:', task.mode || 'DEVELOPMENT');
                console.log('   Priority:', task.priority || 'medium');
                console.log();
                console.log('Description:');
                console.log(task.description || 'No description provided');
                
                if (task.important_files && task.important_files.length > 0) {
                    console.log();
                    console.log('Important Files:');
                    task.important_files.forEach(file => console.log('  -', file));
                }
            } else {
                console.log('📭 No pending tasks found');
                
                // Show in-progress tasks if any
                const inProgressTasks = todoData.tasks.filter(t => t.status === 'in_progress');
                if (inProgressTasks.length > 0) {
                    console.log();
                    console.log('⚡ Tasks in progress:');
                    inProgressTasks.forEach(task => {
                        console.log('  -', task.title, '(ID:', task.id + ')');
                    });
                }
            }
        })
        .catch(error => {
            console.error('❌ Error reading TODO.json:', error.message);
            process.exit(1);
        });
    "
fi