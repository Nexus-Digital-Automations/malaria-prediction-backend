#!/bin/bash

# Task Backup Script
# Usage: ./task-backup.sh [--list|--create|--restore|--cleanup]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
ACTION="list"

while [[ $# -gt 0 ]]; do
    case $1 in
        --list)
            ACTION="list"
            shift
            ;;
        --create)
            ACTION="create"
            shift
            ;;
        --restore)
            ACTION="restore"
            shift
            ;;
        --cleanup)
            ACTION="cleanup"
            shift
            ;;
        --help)
            echo "Usage: $0 [--list|--create|--restore|--cleanup]"
            echo ""
            echo "Manage TaskManager backups"
            echo ""
            echo "Options:"
            echo "  --list                    List available backups (default)"
            echo "  --create                  Create a new backup"
            echo "  --restore                 Restore from latest backup"
            echo "  --cleanup                 Clean up old backups"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                        # List backups"
            echo "  $0 --create               # Create backup"
            echo "  $0 --restore              # Restore from latest"
            echo "  $0 --cleanup              # Clean old backups"
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

case "$ACTION" in
    "list")
        echo "📦 Available Backups"
        echo "═".repeat(40)
        
        node -e "
        const TaskManager = require('./lib/taskManager');
        const taskManager = new TaskManager('./TODO.json');
        
        taskManager.listBackups()
            .then(backups => {
                if (backups.length === 0) {
                    console.log('📭 No backups found');
                    return;
                }
                
                console.log('Found ' + backups.length + ' backups:');
                console.log();
                
                backups.forEach((backup, index) => {
                    console.log(\`\${index + 1}. \${backup.filename}\`);
                    console.log(\`   Date: \${new Date(backup.created).toLocaleString()}\`);
                    console.log(\`   Size: \${backup.size} bytes\`);
                    
                    if (backup.tasks !== undefined) {
                        console.log(\`   Tasks: \${backup.tasks}\`);
                    }
                    
                    if (index < backups.length - 1) {
                        console.log();
                    }
                });
            })
            .catch(error => {
                console.error('❌ Error listing backups:', error.message);
                process.exit(1);
            });
        "
        ;;
    "create")
        echo "💾 Creating backup..."
        
        node -e "
        const TaskManager = require('./lib/taskManager');
        const taskManager = new TaskManager('./TODO.json');
        
        taskManager.createBackup()
            .then(result => {
                console.log('✅ Backup created successfully!');
                console.log('   Filename:', result.filename);
                console.log('   Path:', result.path);
                console.log('   Size:', result.size, 'bytes');
                console.log('   Tasks backed up:', result.taskCount);
            })
            .catch(error => {
                console.error('❌ Error creating backup:', error.message);
                process.exit(1);
            });
        "
        ;;
    "restore")
        echo "🔄 Restoring from backup..."
        echo "⚠️  This will overwrite current TODO.json!"
        echo -n "Continue? (y/N): "
        read -r CONFIRM
        
        if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
            echo "❌ Restore cancelled"
            exit 1
        fi
        
        node -e "
        const TaskManager = require('./lib/taskManager');
        const taskManager = new TaskManager('./TODO.json');
        
        taskManager.restoreFromBackup()
            .then(result => {
                console.log('✅ Restore completed successfully!');
                console.log('   Restored from:', result.backupFile);
                console.log('   Tasks restored:', result.taskCount);
                console.log('   Backup date:', new Date(result.backupDate).toLocaleString());
            })
            .catch(error => {
                console.error('❌ Error restoring backup:', error.message);
                process.exit(1);
            });
        "
        ;;
    "cleanup")
        echo "🧹 Cleaning up old backups..."
        
        node -e "
        const TaskManager = require('./lib/taskManager');
        const taskManager = new TaskManager('./TODO.json');
        
        taskManager.cleanupLegacyBackups()
            .then(result => {
                console.log('✅ Cleanup completed!');
                console.log('   Files removed:', result.filesRemoved);
                console.log('   Space freed:', result.spaceFreed, 'bytes');
                console.log('   Backups kept:', result.backupsKept);
            })
            .catch(error => {
                console.error('❌ Error during cleanup:', error.message);
                process.exit(1);
            });
        "
        ;;
esac