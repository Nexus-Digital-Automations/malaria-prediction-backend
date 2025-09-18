#!/bin/bash

# TaskManager Master Script
# Usage: ./taskmanager.sh <command> [args...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Removed unused setup function for performance

# Function to check and auto-setup if there's an error
check_and_setup_on_error() {
    local current_dir="$(pwd)"
    
    # Skip setup if in test environment or if disabled via env var
    if [[ "$NODE_ENV" == "test" || "$CLAUDE_TASKMANAGER_NO_AUTO_SETUP" == "1" ]]; then
        return 1  # Return error to indicate no setup attempted
    fi
    
    # Check if we're missing critical files
    if [[ ! -f "$current_dir/TODO.json" ]]; then
        echo "⚠️  TODO.json missing - running auto-setup..."
        
        # Run setup script silently in batch mode
        if [[ -x "$PROJECT_ROOT/setup-infinite-hook.js" ]]; then
            node "$PROJECT_ROOT/setup-infinite-hook.js" "$current_dir" --single --batch --no-interactive >/dev/null 2>&1 && {
                echo "✅ Auto-setup completed successfully"
                return 0
            } || {
                echo "❌ Auto-setup failed for $current_dir" >&2
                return 1
            }
        else
            echo "❌ Setup script not found at $PROJECT_ROOT/setup-infinite-hook.js" >&2
            return 1
        fi
    fi
    
    return 1  # No setup needed
}

# Show help if no arguments provided
if [ $# -eq 0 ]; then
    echo "TaskManager CLI - Master Script (with Auto-Setup)"
    echo "================================================="
    echo ""
    echo "🚀 Auto-Setup: TaskManager automatically sets up project infrastructure"
    echo "   - Creates TODO.json if missing"
    echo "   - Sets up development/ directory structure"
    echo "   - Copies mode files from infinite-continue-stop-hook"
    echo "   - Skips setup if project is already configured"
    echo ""
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "Task Management Commands:"
    echo "  current [agent_id]                    Get current task"
    echo "  create --title \"Title\" --description \"Desc\" --mode \"MODE\" [options]"
    echo "  complete <task_id>                    Mark task as completed"
    echo "  status <task_id> <new_status>         Update task status"
    echo "  info <task_id>                        Show task details"
    echo "  list [--status status] [--mode mode] [options]"
    echo "  remove <task_id> [--confirm]          Remove task"
    echo ""
    echo "Task Organization Commands:"
    echo "  move-top <task_id>                    Move task to top priority"
    echo "  move-bottom <task_id>                 Move task to bottom"
    echo "  move-up <task_id>                     Move task up one position"
    echo "  move-down <task_id>                   Move task down one position"
    echo ""
    echo "Task File Management:"
    echo "  add-file <task_id> <file_path>        Add important file to task"
    echo "  remove-file <task_id> <file_path>     Remove file from task"
    echo ""
    echo "Dependencies:"
    echo "  dependencies [--graph] [--executable] [--task task_id]"
    echo ""
    echo "Agent Management Commands:"
    echo "  init [config_json]                    Initialize agent (auto-assigns ID)"
    echo "  agent-register --role \"role\" --session \"session\" [options]"
    echo "  agent-claim <agent_id> <task_id> [priority]"
    echo "  agent-status <agent_id>               Show agent status"
    echo "  agent-list [--active] [--format fmt]  List agents"
    echo ""
    echo "Linter Commands:"
    echo "  linter-check                          Run linter checks on project"
    echo "  linter-clear                          Clear linter feedback (fast by default)"
    echo ""
    echo "Backup & Archive Commands:"
    echo "  backup [--list|--create|--restore|--cleanup]"
    echo "  archive [--list|--stats|--restore task_id|--migrate]"
    echo ""
    echo "Examples:"
    echo "  $0 init                               # Initialize new agent"
    echo "  $0 current                            # Get current task"
    echo "  $0 list --status pending              # List pending tasks"
    echo "  $0 complete task_123                  # Mark task as completed"
    echo "  $0 create --title \"Fix bug\" --description \"Login issue\" --mode \"DEVELOPMENT\""
    echo "  $0 agent-register --role \"development\" --session \"session_123\""
    echo ""
    echo "Environment Variables:"
    echo "  CLAUDE_TASKMANAGER_NO_AUTO_SETUP=1   # Disable auto-setup entirely"
    echo "  NODE_ENV=test                         # Disables auto-setup in test mode"
    echo ""
    echo "For detailed help on any command:"
    echo "  $0 <command> --help"
    exit 0
fi

COMMAND="$1"
shift

case "$COMMAND" in
    "current")
        # Try command first, run setup on error
        "$SCRIPT_DIR/current-task.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/current-task.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "create")
        "$SCRIPT_DIR/task-create.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-create.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "complete")
        "$SCRIPT_DIR/task-complete.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-complete.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "status")
        "$SCRIPT_DIR/task-status.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-status.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "info")
        "$SCRIPT_DIR/task-info.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-info.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "list")
        "$SCRIPT_DIR/task-list.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-list.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "remove")
        "$SCRIPT_DIR/task-remove.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-remove.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "move-top")
        "$SCRIPT_DIR/task-move-top.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-move-top.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "move-bottom")
        "$SCRIPT_DIR/task-move-bottom.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-move-bottom.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "move-up")
        "$SCRIPT_DIR/task-move-up.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-move-up.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "move-down")
        "$SCRIPT_DIR/task-move-down.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-move-down.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "add-file")
        "$SCRIPT_DIR/task-add-file.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-add-file.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "remove-file")
        "$SCRIPT_DIR/task-remove-file.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-remove-file.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "dependencies")
        "$SCRIPT_DIR/task-dependencies.sh" "$@" || {
            if check_and_setup_on_error; then
                exec "$SCRIPT_DIR/task-dependencies.sh" "$@"
            else
                exit 1
            fi
        }
        ;;
    "init")
        exec "$SCRIPT_DIR/agent-init.sh" "$@"
        ;;
    "agent-register")
        exec "$SCRIPT_DIR/agent-register.sh" "$@"
        ;;
    "agent-claim")
        exec "$SCRIPT_DIR/agent-claim-task.sh" "$@"
        ;;
    "agent-status")
        exec "$SCRIPT_DIR/agent-status.sh" "$@"
        ;;
    "agent-list")
        exec "$SCRIPT_DIR/agent-list.sh" "$@"
        ;;
    "backup")
        exec "$SCRIPT_DIR/task-backup.sh" "$@"
        ;;
    "archive")
        exec "$SCRIPT_DIR/task-archive.sh" "$@"
        ;;
    "linter-check")
        exec "$SCRIPT_DIR/linter-check.sh" "$@"
        ;;
    "linter-clear")
        exec "$SCRIPT_DIR/linter-clear.sh" "$@"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Use '$0' (without arguments) to see available commands"
        exit 1
        ;;
esac