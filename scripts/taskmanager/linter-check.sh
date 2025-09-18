#!/bin/bash

# Linter Check Script
# Usage: ./linter-check.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            echo "Usage: $0"
            echo ""
            echo "Check for pending linter feedback in the TaskManager system"
            echo ""
            echo "Options:"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                        # Check for pending linter feedback"
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

echo "🔍 Running linter check on project..."

# Run linter checks directly using the LinterFeedbackGenerator
node -e "
const LinterFeedbackGenerator = require('./lib/linterFeedbackGenerator');
const fs = require('fs');
const path = require('path');

async function runLinterCheck() {
    try {
        const linterGenerator = new LinterFeedbackGenerator();
        
        // Check common development directories
        const dirs = ['src', 'lib', 'components', 'utils', '.'].filter(dir => {
            try {
                return fs.existsSync(dir) && fs.statSync(dir).isDirectory();
            } catch {
                return false;
            }
        });
        
        if (dirs.length === 0) {
            // If no common dirs found, check current directory
            dirs.push('.');
        }
        
        console.log(\`📁 Checking directories: \${dirs.join(', ')}\`);
        console.log();
        
        const result = await linterGenerator.generateFeedback(dirs);
        const feedback = linterGenerator.generateClaudeFeedback(result);
        
        if (feedback.hasIssues) {
            console.log(feedback.title);
            console.log(feedback.message);
            console.log();
            
            if (feedback.details && feedback.details.length > 0) {
                console.log('📋 Detailed Issues:');
                console.log('═'.repeat(50));
                feedback.details.forEach(detail => {
                    console.log(\`📄 \${detail.file}:\`);
                    detail.issues.forEach(issue => {
                        const severity = issue.severity === 'error' ? '❌' : '⚠️';
                        console.log(\`  \${severity} Line \${issue.line}:\${issue.column} - \${issue.message} (\${issue.rule})\`);
                    });
                    console.log();
                });
                console.log('═'.repeat(50));
            }
            
            process.exit(1); // Exit with error to indicate issues found
        } else {
            console.log(feedback.title);
            console.log(feedback.message);
            console.log('✅ All linter checks passed');
        }
    } catch (error) {
        console.error('❌ Error running linter check:', error.message);
        process.exit(1);
    }
}

runLinterCheck();
"