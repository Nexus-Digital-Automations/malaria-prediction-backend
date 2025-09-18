#!/bin/bash

# Agent Registration Script
# Usage: ./agent-register.sh --role "role" --session "session_id" [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TODO_PATH="$PROJECT_ROOT/TODO.json"

# Default values
ROLE=""
SESSION=""
SPECIALIZATION=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
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
        --help)
            echo "Usage: $0 --role \"role\" --session \"session_id\" [options]"
            echo ""
            echo "Required:"
            echo "  --role        Agent role (development, testing, review, etc.)"
            echo "  --session     Agent session ID"
            echo ""
            echo "Optional:"
            echo "  --specialization  Comma-separated list of specializations"
            echo ""
            echo "Example:"
            echo "  $0 --role \"development\" --session \"session_123\" --specialization \"testing,linting\""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$ROLE" ]; then
    echo "Error: --role is required"
    exit 1
fi

if [ -z "$SESSION" ]; then
    echo "Error: --session is required"
    exit 1
fi

if [ ! -f "$TODO_PATH" ]; then
    echo "Error: TODO.json not found at $TODO_PATH"
    exit 1
fi

echo "🔄 Registering agent..."

cd "$PROJECT_ROOT"
node -e "
const AgentManager = require('./lib/agentManager');
const agentManager = new AgentManager('./TODO.json');

const agentConfig = {
  role: '$ROLE',
  sessionId: '$SESSION'
};

if ('$SPECIALIZATION') {
  agentConfig.specialization = '$SPECIALIZATION'.split(',').map(s => s.trim());
}

agentManager.registerAgent(agentConfig)
  .then(agentId => {
    console.log('✅ Agent registered with ID:', agentId);
    process.exit(0);
  })
  .catch(error => {
    console.error('❌ Error:', error.message);
    process.exit(1);
  });
"