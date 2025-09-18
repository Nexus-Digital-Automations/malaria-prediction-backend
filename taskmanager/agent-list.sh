#!/bin/bash

# Agent List Script
# Usage: ./agent-list.sh [--active] [--format fmt]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
ACTIVE_ONLY=false
FORMAT="table"

while [[ $# -gt 0 ]]; do
    case $1 in
        --active)
            ACTIVE_ONLY=true
            shift
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--active] [--format fmt]"
            echo ""
            echo "List agents in the TaskManager system"
            echo ""
            echo "Options:"
            echo "  --active                  Show only active agents"
            echo "  --format <format>         Output format (table, json, compact)"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                        # List all agents"
            echo "  $0 --active               # List only active agents"
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

echo "👥 Listing agents..."
if [[ "$ACTIVE_ONLY" == true ]]; then
    echo "   Filter: Active only"
fi
echo "   Format: $FORMAT"
echo

# List agents based on format
case "$FORMAT" in
    "json")
        if [[ "$ACTIVE_ONLY" == true ]]; then
            node -e "
            const result = require('./initialize-agent.js').listActiveAgents();
            result.then(data => console.log(JSON.stringify(data, null, 2)))
                .catch(error => {
                    console.error('❌ Error listing agents:', error.message);
                    process.exit(1);
                });
            "
        else
            node -e "
            const AgentRegistry = require('./lib/agentRegistry');
            const registry = new AgentRegistry();
            
            try {
                const agents = registry.getAllAgents();
                console.log(JSON.stringify(agents, null, 2));
            } catch (error) {
                console.error('❌ Error listing agents:', error.message);
                process.exit(1);
            }
            "
        fi
        ;;
    "compact")
        if [[ "$ACTIVE_ONLY" == true ]]; then
            node -e "
            const result = require('./initialize-agent.js').listActiveAgents();
            result.then(data => {
                if (data.activeAgents && data.activeAgents.length > 0) {
                    console.log('👥 Active Agents (' + data.activeAgents.length + ')');
                    data.activeAgents.forEach((agent, index) => {
                        console.log(\`\${index + 1}. \${agent.agentId} - \${agent.role} (\${agent.totalRequests} requests)\`);
                    });
                } else {
                    console.log('📭 No active agents found');
                }
            }).catch(error => {
                console.error('❌ Error listing agents:', error.message);
                process.exit(1);
            });
            "
        else
            echo "Compact format for all agents not implemented. Use --active or --format table."
        fi
        ;;
    "table"|*)
        if [[ "$ACTIVE_ONLY" == true ]]; then
            node -e "
            const result = require('./initialize-agent.js').listActiveAgents();
            result.then(data => {
                if (data.activeAgents && data.activeAgents.length > 0) {
                    console.log('👥 Active Agents (' + data.activeAgents.length + ')');
                    console.log('═'.repeat(70));
                    
                    data.activeAgents.forEach((agent, index) => {
                        console.log(\`\${index + 1}. Agent ID: \${agent.agentId}\`);
                        console.log(\`   Role: \${agent.role}\`);
                        console.log(\`   Session: \${agent.sessionId || 'N/A'}\`);
                        console.log(\`   Requests: \${agent.totalRequests}\`);
                        console.log(\`   Last Active: \${new Date(agent.lastActivity).toLocaleString()}\`);
                        
                        if (agent.specialization && agent.specialization.length > 0) {
                            console.log(\`   Specialization: \${agent.specialization.join(', ')}\`);
                        }
                        
                        if (index < data.activeAgents.length - 1) {
                            console.log('─'.repeat(40));
                        }
                    });
                    console.log('═'.repeat(70));
                } else {
                    console.log('📭 No active agents found');
                }
            }).catch(error => {
                console.error('❌ Error listing agents:', error.message);
                process.exit(1);
            });
            "
        else
            node -e "
            const AgentRegistry = require('./lib/agentRegistry');
            const registry = new AgentRegistry();
            
            try {
                const agents = registry.getAllAgents();
                if (agents && agents.length > 0) {
                    console.log('👥 All Agents (' + agents.length + ')');
                    console.log('═'.repeat(70));
                    
                    agents.forEach((agent, index) => {
                        const isActive = agent.lastActivity && 
                            (Date.now() - new Date(agent.lastActivity).getTime()) < 2 * 60 * 60 * 1000;
                        const status = isActive ? '🟢 Active' : '🔴 Inactive';
                        
                        console.log(\`\${index + 1}. Agent ID: \${agent.agentId} \${status}\`);
                        console.log(\`   Role: \${agent.role}\`);
                        console.log(\`   Session: \${agent.sessionId || 'N/A'}\`);
                        console.log(\`   Total Requests: \${agent.totalRequests || 0}\`);
                        
                        if (agent.lastActivity) {
                            console.log(\`   Last Active: \${new Date(agent.lastActivity).toLocaleString()}\`);
                        }
                        
                        if (agent.specialization && agent.specialization.length > 0) {
                            console.log(\`   Specialization: \${agent.specialization.join(', ')}\`);
                        }
                        
                        if (index < agents.length - 1) {
                            console.log('─'.repeat(40));
                        }
                    });
                    console.log('═'.repeat(70));
                } else {
                    console.log('📭 No agents found');
                }
            } catch (error) {
                console.error('❌ Error listing agents:', error.message);
                process.exit(1);
            }
            "
        fi
        ;;
esac