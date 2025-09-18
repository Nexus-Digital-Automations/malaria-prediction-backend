#!/bin/bash

# Task Dependencies Script
# Usage: ./task-dependencies.sh [--graph] [--executable] [--task task_id]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
SHOW_GRAPH=false
SHOW_EXECUTABLE=false
TASK_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --graph)
            SHOW_GRAPH=true
            shift
            ;;
        --executable)
            SHOW_EXECUTABLE=true
            shift
            ;;
        --task)
            TASK_ID="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--graph] [--executable] [--task task_id]"
            echo ""
            echo "Show task dependencies and dependency information"
            echo ""
            echo "Options:"
            echo "  --graph                   Show dependency graph visualization"
            echo "  --executable              Show only executable tasks (no unmet dependencies)"
            echo "  --task <task_id>          Show dependencies for specific task"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                        # Show basic dependency info"
            echo "  $0 --graph                # Show dependency graph"
            echo "  $0 --executable           # Show executable tasks only"
            echo "  $0 --task task_123        # Show dependencies for task_123"
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

if [[ "$SHOW_GRAPH" == true ]]; then
    echo "📊 Task Dependency Graph"
    echo "══════════════════════════════════════════════════"
    
    node -e "
    const TaskManager = require('./lib/taskManager');
    const taskManager = new TaskManager('./TODO.json');
    
    taskManager.buildDependencyGraph()
        .then(graph => {
            console.log(graph.tree || 'No dependency graph available');
        })
        .catch(error => {
            console.error('❌ Error building dependency graph:', error.message);
            process.exit(1);
        });
    "
elif [[ "$SHOW_EXECUTABLE" == true ]]; then
    echo "🚀 Executable Tasks (No Unmet Dependencies)"
    echo "══════════════════════════════════════════════════"
    
    node -e "
    const TaskManager = require('./lib/taskManager');
    const taskManager = new TaskManager('./TODO.json');
    
    taskManager.getExecutableTasks()
        .then(executableTasks => {
            if (executableTasks.length === 0) {
                console.log('📭 No executable tasks found');
                console.log('All pending tasks have unmet dependencies');
                return;
            }
            
            console.log('Found ' + executableTasks.length + ' executable tasks:');
            console.log();
            
            executableTasks.forEach((task, index) => {
                const statusIcon = task.status === 'pending' ? '⏳' : 
                                  task.status === 'in_progress' ? '⚡' :
                                  task.status === 'completed' ? '✅' : '❌';
                
                console.log(\`\${index + 1}. \${statusIcon} \${task.title}\`);
                console.log(\`   ID: \${task.id}\`);
                console.log(\`   Status: \${task.status}\`);
                console.log(\`   Mode: \${task.mode || 'DEVELOPMENT'}\`);
                console.log(\`   Priority: \${task.priority || 'medium'}\`);
                
                if (index < executableTasks.length - 1) {
                    console.log();
                }
            });
        })
        .catch(error => {
            console.error('❌ Error getting executable tasks:', error.message);
            process.exit(1);
        });
    "
elif [[ -n "$TASK_ID" ]]; then
    echo "🔗 Dependencies for Task: $TASK_ID"
    echo "══════════════════════════════════════════════════"
    
    node -e "
    const TaskManager = require('./lib/taskManager');
    const taskManager = new TaskManager('./TODO.json');
    
    taskManager.readTodo()
        .then(todoData => {
            const task = todoData.tasks.find(t => t.id === '$TASK_ID');
            if (!task) {
                throw new Error('Task not found: $TASK_ID');
            }
            
            console.log('📋 Task Details:');
            console.log('   ID:', task.id);
            console.log('   Title:', task.title);
            console.log('   Status:', task.status);
            console.log();
            
            if (!task.dependencies || task.dependencies.length === 0) {
                console.log('✅ No dependencies - task is ready to execute');
                return;
            }
            
            console.log('🔗 Dependencies (' + task.dependencies.length + '):');
            console.log();
            
            const depPromises = task.dependencies.map(depId => {
                const depTask = todoData.tasks.find(t => t.id === depId);
                if (!depTask) {
                    return Promise.resolve({
                        id: depId,
                        title: 'Unknown Task',
                        status: 'missing',
                        found: false
                    });
                }
                return Promise.resolve(depTask);
            });
            
            return Promise.all(depPromises);
        })
        .then(dependencies => {
            if (!dependencies) return;
            
            let metDependencies = 0;
            dependencies.forEach((dep, index) => {
                const statusIcon = !dep.found ? '❌' :
                                  dep.status === 'completed' ? '✅' : '⏳';
                const statusText = !dep.found ? 'MISSING' :
                                  dep.status === 'completed' ? 'COMPLETED' : 'PENDING';
                
                console.log(\`\${index + 1}. \${statusIcon} \${dep.title}\`);
                console.log(\`   ID: \${dep.id}\`);
                console.log(\`   Status: \${statusText}\`);
                
                if (dep.found && dep.status === 'completed') {
                    metDependencies++;
                }
                
                if (index < dependencies.length - 1) {
                    console.log();
                }
            });
            
            console.log();
            console.log('📊 Dependency Status:');
            console.log(\`   Met: \${metDependencies}/\${dependencies.length}\`);
            
            if (metDependencies === dependencies.length) {
                console.log('   ✅ All dependencies satisfied - task can be executed');
            } else {
                console.log('   ⏳ Unmet dependencies - task cannot be executed yet');
            }
        })
        .catch(error => {
            console.error('❌ Error getting task dependencies:', error.message);
            process.exit(1);
        });
    "
else
    echo "📊 Task Dependency Summary"
    echo "══════════════════════════════════════════════════"
    
    node -e "
    const TaskManager = require('./lib/taskManager');
    const taskManager = new TaskManager('./TODO.json');
    
    Promise.all([
        taskManager.readTodo(),
        taskManager.getExecutableTasks()
    ])
        .then(([todoData, executableTasks]) => {
            const allTasks = todoData.tasks;
            const tasksWithDeps = allTasks.filter(t => t.dependencies && t.dependencies.length > 0);
            const completedTasks = allTasks.filter(t => t.status === 'completed');
            const pendingTasks = allTasks.filter(t => t.status === 'pending');
            
            console.log('📋 Overview:');
            console.log('   Total Tasks:', allTasks.length);
            console.log('   Completed:', completedTasks.length);
            console.log('   Pending:', pendingTasks.length);
            console.log('   With Dependencies:', tasksWithDeps.length);
            console.log('   Executable (No unmet deps):', executableTasks.length);
            console.log();
            
            if (tasksWithDeps.length > 0) {
                console.log('🔗 Tasks with Dependencies:');
                console.log();
                
                tasksWithDeps.forEach((task, index) => {
                    const statusIcon = task.status === 'completed' ? '✅' : 
                                      executableTasks.find(et => et.id === task.id) ? '🚀' : '⏳';
                    
                    console.log(\`\${index + 1}. \${statusIcon} \${task.title}\`);
                    console.log(\`   ID: \${task.id}\`);
                    console.log(\`   Dependencies: \${task.dependencies.length}\`);
                    console.log(\`   Status: \${task.status}\`);
                    
                    if (index < tasksWithDeps.length - 1) {
                        console.log();
                    }
                });
            }
            
            console.log();
            console.log('💡 Use --graph to see dependency visualization');
            console.log('💡 Use --executable to see ready-to-run tasks');
            console.log('💡 Use --task <id> to see specific task dependencies');
        })
        .catch(error => {
            console.error('❌ Error getting dependency summary:', error.message);
            process.exit(1);
        });
    "
fi