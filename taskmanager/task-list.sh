#!/bin/bash

# Task List Script  
# Usage: ./task-list.sh [--status status] [--mode mode] [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Initialize variables
STATUS_FILTER=""
MODE_FILTER=""
LIMIT=""
FORMAT="table"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --status)
            STATUS_FILTER="$2"
            shift 2
            ;;
        --mode)
            MODE_FILTER="$2"
            shift 2
            ;;
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--status status] [--mode mode] [options]"
            echo ""
            echo "List tasks from the TaskManager system"
            echo ""
            echo "Options:"
            echo "  --status <status>         Filter by status (pending, in_progress, completed, blocked)"
            echo "  --mode <mode>             Filter by execution mode (DEVELOPMENT, TESTING, etc.)"
            echo "  --limit <number>          Limit number of results"
            echo "  --format <format>         Output format (table, json, compact)"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                        # List all tasks"
            echo "  $0 --status pending       # List only pending tasks"
            echo "  $0 --mode TESTING         # List only testing tasks"
            echo "  $0 --status pending --limit 5  # List first 5 pending tasks"
            echo "  $0 --format json          # Output in JSON format"
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

# Change to project root
cd "$PROJECT_ROOT"

# Build the filter query
QUERY="{"
FIRST=true

if [[ -n "$STATUS_FILTER" ]]; then
    QUERY="${QUERY}\"status\": \"$STATUS_FILTER\""
    FIRST=false
fi

if [[ -n "$MODE_FILTER" ]]; then
    if [[ "$FIRST" == false ]]; then
        QUERY="${QUERY}, "
    fi
    QUERY="${QUERY}\"mode\": \"$MODE_FILTER\""
    FIRST=false
fi

QUERY="${QUERY}}"

# List tasks based on format
case "$FORMAT" in
    "json")
        node -e "
        const TaskManager = require('./lib/taskManager');
        const taskManager = new TaskManager('./TODO.json');
        const query = $QUERY;
        
        taskManager.queryTasks(query)
            .then(tasks => {
                let results = tasks;
                if ('$LIMIT' !== '') {
                    results = tasks.slice(0, parseInt('$LIMIT'));
                }
                console.log(JSON.stringify(results, null, 2));
            })
            .catch(error => {
                console.error('❌ Error listing tasks:', error.message);
                process.exit(1);
            });
        "
        ;;
    "compact")
        node -e "
        const TaskManager = require('./lib/taskManager');
        const taskManager = new TaskManager('./TODO.json');
        const query = $QUERY;
        
        taskManager.queryTasks(query)
            .then(tasks => {
                let results = tasks;
                if ('$LIMIT' !== '') {
                    results = tasks.slice(0, parseInt('$LIMIT'));
                }
                
                console.log('📋 Tasks (' + results.length + ')');
                results.forEach((task, index) => {
                    const status = task.status === 'pending' ? '⏳' : 
                                  task.status === 'in_progress' ? '⚡' :
                                  task.status === 'completed' ? '✅' : '❌';
                    console.log(\`\${index + 1}. \${status} \${task.title} (ID: \${task.id})\`);
                });
            })
            .catch(error => {
                console.error('❌ Error listing tasks:', error.message);
                process.exit(1);
            });
        "
        ;;
    "table"|*)
        node -e "
        const TaskManager = require('./lib/taskManager');
        const taskManager = new TaskManager('./TODO.json');
        const query = $QUERY;
        
        taskManager.queryTasks(query)
            .then(tasks => {
                let results = tasks;
                if ('$LIMIT' !== '') {
                    results = tasks.slice(0, parseInt('$LIMIT'));
                }
                
                if (results.length === 0) {
                    console.log('📭 No tasks found matching criteria');
                    return;
                }
                
                console.log('📋 Task List (' + results.length + ' tasks)');
                console.log('═'.repeat(80));
                
                results.forEach((task, index) => {
                    const status = task.status === 'pending' ? '⏳ Pending' : 
                                  task.status === 'in_progress' ? '⚡ In Progress' :
                                  task.status === 'completed' ? '✅ Completed' : '❌ Blocked';
                    
                    console.log(\`\${index + 1}. \${task.title}\`);
                    console.log(\`   ID: \${task.id}\`);
                    console.log(\`   Status: \${status}\`);
                    console.log(\`   Mode: \${task.mode || 'DEVELOPMENT'}\`);
                    console.log(\`   Priority: \${task.priority || 'medium'}\`);
                    
                    if (task.assigned_agent) {
                        console.log(\`   Agent: \${task.assigned_agent}\`);
                    }
                    
                    if (task.description && task.description.length > 100) {
                        console.log(\`   Description: \${task.description.substring(0, 97)}...\`);
                    } else if (task.description) {
                        console.log(\`   Description: \${task.description}\`);
                    }
                    
                    if (index < results.length - 1) {
                        console.log('─'.repeat(40));
                    }
                });
                console.log('═'.repeat(80));
            })
            .catch(error => {
                console.error('❌ Error listing tasks:', error.message);
                process.exit(1);
            });
        "
        ;;
esac