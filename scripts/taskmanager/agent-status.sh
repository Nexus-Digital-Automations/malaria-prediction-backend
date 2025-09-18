#!/bin/bash

# Agent Status Script
# Usage: ./agent-status.sh <agent_id>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
AGENT_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            echo "Usage: $0 <agent_id>"
            echo ""
            echo "Show detailed status for a specific agent"
            echo ""
            echo "Arguments:"
            echo "  agent_id                  ID of the agent to show status for"
            echo ""
            echo "Options:"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 agent_1                # Show status for agent_1"
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
                echo "Multiple agent IDs provided. Only one agent can be shown at a time."
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

# Change to project root
cd "$PROJECT_ROOT"

echo "🔍 Getting agent status..."
echo "   Agent ID: $AGENT_ID"
echo

# Show agent status
node -e "
const AgentRegistry = require('./lib/agentRegistry');
const TaskManager = require('./lib/taskManager');

const registry = new AgentRegistry();
const taskManager = new TaskManager('./TODO.json');

Promise.all([
    registry.getAgentInfo('$AGENT_ID'),
    taskManager.getTasksForAgent('$AGENT_ID'),
    taskManager.getCurrentTask('$AGENT_ID')
])
    .then(([agentInfo, assignedTasks, currentTask]) => {
        if (!agentInfo) {
            throw new Error('Agent not found: $AGENT_ID');
        }
        
        console.log('👤 Agent Status');
        console.log('═'.repeat(60));
        console.log('ID:', agentInfo.agentId);
        console.log('Role:', agentInfo.role);
        console.log('Session:', agentInfo.sessionId || 'N/A');
        
        const isActive = agentInfo.lastActivity && 
            (Date.now() - new Date(agentInfo.lastActivity).getTime()) < 2 * 60 * 60 * 1000;
        const status = isActive ? '🟢 Active' : '🔴 Inactive';
        console.log('Status:', status);
        
        if (agentInfo.lastActivity) {
            console.log('Last Active:', new Date(agentInfo.lastActivity).toLocaleString());
        }
        
        console.log('Total Requests:', agentInfo.totalRequests || 0);
        
        if (agentInfo.specialization && agentInfo.specialization.length > 0) {
            console.log('Specialization:', agentInfo.specialization.join(', '));
        }
        
        console.log();
        console.log('📋 Current Task');
        console.log('─'.repeat(30));
        if (currentTask) {
            console.log('ID:', currentTask.id);
            console.log('Title:', currentTask.title);
            console.log('Status:', currentTask.status);
            console.log('Mode:', currentTask.mode || 'DEVELOPMENT');
            console.log('Priority:', currentTask.priority || 'medium');
        } else {
            console.log('No current task assigned');
        }
        
        console.log();
        console.log('📝 Assigned Tasks (' + assignedTasks.length + ')');
        console.log('─'.repeat(30));
        if (assignedTasks.length > 0) {
            assignedTasks.forEach((task, index) => {
                const statusIcon = task.status === 'pending' ? '⏳' : 
                                  task.status === 'in_progress' ? '⚡' :
                                  task.status === 'completed' ? '✅' : '❌';
                console.log(\`\${index + 1}. \${statusIcon} \${task.title} (ID: \${task.id})\`);
                console.log(\`   Status: \${task.status} | Mode: \${task.mode || 'DEVELOPMENT'}\`);
                
                if (index < assignedTasks.length - 1) {
                    console.log();
                }
            });
        } else {
            console.log('No tasks assigned to this agent');
        }
        
        console.log('═'.repeat(60));
    })
    .catch(error => {
        console.error('❌ Error getting agent status:', error.message);
        process.exit(1);
    });
"