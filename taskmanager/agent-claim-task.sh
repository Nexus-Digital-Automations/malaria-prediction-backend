#!/bin/bash

# Agent Claim Task Script
# Usage: ./agent-claim-task.sh <agent_id> <task_id> [priority]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
AGENT_ID=""
TASK_ID=""
PRIORITY="normal"

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            echo "Usage: $0 <agent_id> <task_id> [priority]"
            echo ""
            echo "Claim a task for a specific agent"
            echo ""
            echo "Arguments:"
            echo "  agent_id                  ID of the agent claiming the task"
            echo "  task_id                   ID of the task to claim"
            echo "  priority                  Priority level (low, normal, high) [default: normal]"
            echo ""
            echo "Options:"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 agent_1 task_123       # Agent_1 claims task_123 with normal priority"
            echo "  $0 agent_2 task_456 high  # Agent_2 claims task_456 with high priority"
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
            elif [[ -z "$TASK_ID" ]]; then
                TASK_ID="$1"
            elif [[ -z "$PRIORITY" || "$PRIORITY" == "normal" ]]; then
                PRIORITY="$1"
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
if [[ -z "$AGENT_ID" ]]; then
    echo "Error: agent_id is required"
    echo "Use --help for usage information"
    exit 1
fi

if [[ -z "$TASK_ID" ]]; then
    echo "Error: task_id is required"
    echo "Use --help for usage information"
    exit 1
fi

# Validate priority
case "$PRIORITY" in
    low|normal|high)
        # Valid priority
        ;;
    *)
        echo "Error: Invalid priority '$PRIORITY'"
        echo "Valid priorities: low, normal, high"
        exit 1
        ;;
esac

# Change to project root
cd "$PROJECT_ROOT"

echo "🎯 Agent claiming task..."
echo "   Agent ID: $AGENT_ID"
echo "   Task ID: $TASK_ID"
echo "   Priority: $PRIORITY"
echo

# Claim the task
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
        
        if (task.assigned_agent) {
            console.log('   Currently Assigned To:', task.assigned_agent);
        }
        
        // Attempt to claim the task
        return taskManager.claimTask('$TASK_ID', '$AGENT_ID', '$PRIORITY');
    })
    .then(claimResult => {
        if (claimResult.success) {
            console.log('✅ Task claimed successfully!');
            console.log('   Agent:', '$AGENT_ID');
            console.log('   Task:', claimResult.task.title);
            console.log('   Status:', claimResult.task.status);
            console.log('   Priority:', claimResult.priority);
            
            if (claimResult.task.status === 'in_progress') {
                console.log('🚀 Task is now in progress');
            }
        } else {
            console.log('❌ Failed to claim task');
            console.log('   Reason:', claimResult.reason || 'Unknown reason');
            
            if (claimResult.reason === 'Task already assigned') {
                console.log('   Current assignee:', claimResult.currentAgent);
            } else if (claimResult.reason === 'Unmet dependencies') {
                console.log('   Complete dependencies first');
            }
            
            process.exit(1);
        }
    })
    .catch(error => {
        console.error('❌ Error claiming task:', error.message);
        process.exit(1);
    });
"