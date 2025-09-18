#!/bin/bash

# Agent Initialization Script
# Usage: ./agent-init.sh [config_json] [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default config for agent initialization
CONFIG_JSON='{}'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            echo "Usage: $0 [config_json] [options]"
            echo ""
            echo "Initialize a new agent with automatic ID assignment"
            echo ""
            echo "Arguments:"
            echo "  config_json               Optional JSON configuration for agent"
            echo ""
            echo "Options:"
            echo "  --role <role>             Set agent role (development, testing, review, etc.)"
            echo "  --session <session_id>    Set agent session ID"
            echo "  --specialization <list>   Comma-separated specializations"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Initialize with default config"
            echo "  $0 --role development                 # Initialize development agent"
            echo "  $0 --role testing --session test_123  # Initialize with specific config"
            echo "  $0 '{\"role\": \"development\", \"sessionId\": \"dev_workflow\"}'"
            echo ""
            echo "The agent will be automatically assigned an ID (agent_1, agent_2, etc.)"
            exit 0
            ;;
        --role)
            ROLE="$2"
            shift 2
            ;;
        --session)
            SESSION="$2"
            shift 2
            ;;
        --specialization)
            SPECIALIZATION="$2"
            shift 2
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            # First positional argument is treated as config JSON
            if [[ "$CONFIG_JSON" == "{}" ]]; then
                CONFIG_JSON="$1"
            else
                echo "Multiple config arguments provided. Use --help for usage."
                exit 1
            fi
            shift
            ;;
    esac
done

# Build config from individual options if provided
if [[ -n "$ROLE" ]] || [[ -n "$SESSION" ]] || [[ -n "$SPECIALIZATION" ]]; then
    # Convert to JSON using jq-like construction
    CONFIG_JSON="{"
    FIRST=true
    
    if [[ -n "$ROLE" ]]; then
        CONFIG_JSON="${CONFIG_JSON}\"role\": \"$ROLE\""
        FIRST=false
    fi
    
    if [[ -n "$SESSION" ]]; then
        if [[ "$FIRST" == false ]]; then
            CONFIG_JSON="${CONFIG_JSON}, "
        fi
        CONFIG_JSON="${CONFIG_JSON}\"sessionId\": \"$SESSION\""
        FIRST=false
    fi
    
    if [[ -n "$SPECIALIZATION" ]]; then
        if [[ "$FIRST" == false ]]; then
            CONFIG_JSON="${CONFIG_JSON}, "
        fi
        # Convert comma-separated list to JSON array
        SPEC_ARRAY="["
        IFS=',' read -ra SPECS <<< "$SPECIALIZATION"
        for i in "${!SPECS[@]}"; do
            SPEC="${SPECS[i]// /}"  # Remove spaces
            if [[ $i -gt 0 ]]; then
                SPEC_ARRAY="${SPEC_ARRAY}, "
            fi
            SPEC_ARRAY="${SPEC_ARRAY}\"$SPEC\""
        done
        SPEC_ARRAY="${SPEC_ARRAY}]"
        CONFIG_JSON="${CONFIG_JSON}\"specialization\": $SPEC_ARRAY"
    fi
    
    CONFIG_JSON="${CONFIG_JSON}}"
fi

echo "🚀 Initializing agent..."
echo "📋 Config: $CONFIG_JSON"

# Change to project root and call initialize-agent.js
cd "$PROJECT_ROOT"

# Call the initialization endpoint
RESULT=$(node initialize-agent.js init "$CONFIG_JSON" 2>/dev/null)

# Check if the result contains success information
if echo "$RESULT" | grep -q '"success": true'; then
    AGENT_ID=$(echo "$RESULT" | grep -o '"agentId": "[^"]*"' | cut -d'"' -f4)
    ROLE_OUTPUT=$(echo "$RESULT" | grep -o '"role": "[^"]*"' | cut -d'"' -f4)
    SESSION_OUTPUT=$(echo "$RESULT" | grep -o '"sessionId": "[^"]*"' | cut -d'"' -f4)
    
    echo "✅ Agent initialized successfully!"
    echo "   Agent ID: $AGENT_ID"
    echo "   Role: $ROLE_OUTPUT"
    echo "   Session: $SESSION_OUTPUT"
    
    # Set environment variable for convenience
    echo ""
    echo "💡 To use this agent in subsequent commands:"
    echo "   export CLAUDE_AGENT_ID=\"$AGENT_ID\""
    echo "   # Then use: ./scripts/taskmanager/taskmanager.sh current \$CLAUDE_AGENT_ID"
    
    exit 0
else
    echo "❌ Agent initialization failed"
    echo "$RESULT" | grep -o '"error": "[^"]*"' | cut -d'"' -f4 || echo "Unknown error occurred"
    exit 1
fi