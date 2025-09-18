#!/bin/bash

# Task Archive Script
# Usage: ./task-archive.sh [--list|--stats|--restore task_id|--migrate]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
ACTION="list"
TASK_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --list)
            ACTION="list"
            shift
            ;;
        --stats)
            ACTION="stats"
            shift
            ;;
        --restore)
            ACTION="restore"
            TASK_ID="$2"
            shift 2
            ;;
        --migrate)
            ACTION="migrate"
            shift
            ;;
        --help)
            echo "Usage: $0 [--list|--stats|--restore task_id|--migrate]"
            echo ""
            echo "Manage archived tasks in DONE.json"
            echo ""
            echo "Options:"
            echo "  --list                    List archived tasks (default)"
            echo "  --stats                   Show archive statistics"
            echo "  --restore <task_id>       Restore task from archive"
            echo "  --migrate                 Migrate completed tasks from TODO.json to DONE.json"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                        # List archived tasks"
            echo "  $0 --stats                # Show statistics"
            echo "  $0 --restore task_123     # Restore task_123 from archive"
            echo "  $0 --migrate              # Migrate completed tasks"
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
        echo "📁 Archived Tasks (DONE.json)"
        echo "═".repeat(50)
        
        node -e "
        const TaskManager = require('./lib/taskManager');
        const taskManager = new TaskManager('./TODO.json');
        
        taskManager.getCompletedTasks({ limit: 20 })
            .then(completedTasks => {
                if (completedTasks.length === 0) {
                    console.log('📭 No archived tasks found');
                    console.log('💡 Use --migrate to move completed tasks from TODO.json');
                    return;
                }
                
                console.log('Found ' + completedTasks.length + ' archived tasks (showing latest 20):');
                console.log();
                
                completedTasks.forEach((task, index) => {
                    console.log(\`\${index + 1}. ✅ \${task.title}\`);
                    console.log(\`   ID: \${task.id}\`);
                    console.log(\`   Mode: \${task.mode || 'DEVELOPMENT'}\`);
                    
                    if (task.completed_at) {
                        console.log(\`   Completed: \${new Date(task.completed_at).toLocaleString()}\`);
                    }
                    
                    if (task.assigned_agent) {
                        console.log(\`   Agent: \${task.assigned_agent}\`);
                    }
                    
                    if (index < completedTasks.length - 1) {
                        console.log();
                    }
                });
                
                console.log();
                console.log('💡 Use --stats to see detailed statistics');
                console.log('💡 Use --restore <task_id> to restore a task');
            })
            .catch(error => {
                console.error('❌ Error listing archived tasks:', error.message);
                process.exit(1);
            });
        "
        ;;
    "stats")
        echo "📊 Archive Statistics"
        echo "═".repeat(40)
        
        node -e "
        const TaskManager = require('./lib/taskManager');
        const taskManager = new TaskManager('./TODO.json');
        
        taskManager.getCompletionStats()
            .then(stats => {
                console.log('📈 Completion Statistics:');
                console.log('   Total Completed Tasks:', stats.totalCompleted || 0);
                console.log('   This Week:', stats.thisWeek || 0);
                console.log('   This Month:', stats.thisMonth || 0);
                console.log('   Average per Day:', (stats.averagePerDay || 0).toFixed(1));
                
                if (stats.byMode) {
                    console.log();
                    console.log('📋 By Mode:');
                    Object.entries(stats.byMode).forEach(([mode, count]) => {
                        console.log(\`   \${mode}: \${count}\`);
                    });
                }
                
                if (stats.byAgent) {
                    console.log();
                    console.log('👤 By Agent:');
                    Object.entries(stats.byAgent).forEach(([agent, count]) => {
                        console.log(\`   \${agent}: \${count}\`);
                    });
                }
                
                if (stats.recentActivity) {
                    console.log();
                    console.log('📅 Recent Activity (Last 7 Days):');
                    stats.recentActivity.forEach(day => {
                        console.log(\`   \${day.date}: \${day.count} tasks\`);
                    });
                }
            })
            .catch(error => {
                console.error('❌ Error getting archive statistics:', error.message);
                process.exit(1);
            });
        "
        ;;
    "restore")
        if [[ -z "$TASK_ID" ]]; then
            echo "Error: task_id is required for restore"
            echo "Use --help for usage information"
            exit 1
        fi
        
        echo "🔄 Restoring task from archive..."
        echo "   Task ID: $TASK_ID"
        
        node -e "
        const TaskManager = require('./lib/taskManager');
        const taskManager = new TaskManager('./TODO.json');
        
        taskManager.restoreCompletedTask('$TASK_ID')
            .then(restored => {
                if (restored) {
                    console.log('✅ Task restored successfully!');
                    console.log('📤 Task moved back to TODO.json');
                    console.log('🔄 Task status reset to pending');
                } else {
                    console.log('❌ Task not found in archive or could not be restored');
                    process.exit(1);
                }
            })
            .catch(error => {
                console.error('❌ Error restoring task:', error.message);
                process.exit(1);
            });
        "
        ;;
    "migrate")
        echo "📦 Migrating completed tasks..."
        echo "🔄 Moving completed tasks from TODO.json to DONE.json"
        
        node -e "
        const TaskManager = require('./lib/taskManager');
        const taskManager = new TaskManager('./TODO.json');
        
        taskManager.migrateCompletedTasks()
            .then(result => {
                console.log('✅ Migration completed!');
                console.log('   Tasks migrated:', result.tasksMigrated);
                console.log('   Tasks already archived:', result.alreadyArchived);
                console.log('   Total in archive:', result.totalInArchive);
                
                if (result.tasksMigrated > 0) {
                    console.log();
                    console.log('📁 Migrated tasks:');
                    result.migratedTasks.forEach((task, index) => {
                        console.log(\`   \${index + 1}. \${task.title} (ID: \${task.id})\`);
                    });
                }
            })
            .catch(error => {
                console.error('❌ Error during migration:', error.message);
                process.exit(1);
            });
        "
        ;;
esac