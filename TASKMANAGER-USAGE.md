# TaskManager Script Usage Guide

Complete guide for using `taskmanager-api.js` - the intelligent task orchestration system for Claude Code projects.

## Table of Contents

- [Overview](#overview)
- [Basic Usage](#basic-usage)
- [Getting Help](#getting-help)
- [Task Management](#task-management)
- [Agent Operations](#agent-operations)
- [Stop Hook Integration](#stop-hook-integration)
- [Command Reference](#command-reference)
- [Troubleshooting](#troubleshooting)

---

## Overview

The TaskManager script (`taskmanager-api.js`) is a command-line tool that provides:

✅ **Task Lifecycle Management** - Create, update, query, and complete tasks
✅ **Agent Coordination** - Multi-agent task assignment and tracking
✅ **Stop Hook Integration** - Automated continuous operation via Claude Code
✅ **Quality Validation** - Built-in validation requirements for task completion
✅ **Real-Time Status** - Instant visibility into project progress

### File Locations

**Global TaskManager:**
```
/Users/jeremyparker/infinite-continue-stop-hook/taskmanager-api.js
```

**Project-Local TaskManager:**
```
./taskmanager-api.js  (in each deployed project)
```

---

## Basic Usage

### Command Structure

```bash
timeout <seconds>s node <path-to-taskmanager-api.js> --project-root "$(pwd)" <command> [arguments]
```

**Components:**
- `timeout <seconds>s` - Prevents hanging (recommended: 10s for queries, 30s for operations)
- `node` - Node.js runtime
- `<path-to-taskmanager-api.js>` - Path to the script
- `--project-root "$(pwd)"` - Current project directory
- `<command>` - TaskManager command to execute
- `[arguments]` - Command-specific arguments

### Your First Commands

```bash
# Get help
timeout 10s node ./taskmanager-api.js guide

# Check project status
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats

# List all available commands
timeout 10s node ./taskmanager-api.js methods
```

---

## Getting Help

### Built-In Documentation

#### `guide` - Comprehensive Documentation
Get complete TaskManager documentation:

```bash
timeout 10s node ./taskmanager-api.js guide
```

**Output:** Full API documentation including all commands, parameters, and examples.

#### `methods` - List All Commands
See all available API methods:

```bash
timeout 10s node ./taskmanager-api.js methods
```

**Output:** List of all available commands with brief descriptions.

### Understanding Output

All commands return JSON responses:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { /* command-specific data */ }
}
```

**Common Fields:**
- `success` - Boolean indicating if operation succeeded
- `message` - Human-readable status message
- `data` / `task` / `tasks` - Command-specific results
- `error` - Error details if `success: false`

---

## Task Management

### Checking Task Status

#### Get Overall Statistics

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats
```

**Example Output:**
```json
{
  "success": true,
  "statistics": {
    "total_tasks": 15,
    "by_status": {
      "completed": 8,
      "approved": 3,
      "in-progress": 2,
      "suggested": 2
    },
    "by_priority": {
      "high": 5,
      "normal": 8,
      "low": 2
    },
    "by_type": {
      "feature": 10,
      "error": 3,
      "test": 2
    },
    "completion_rate": 53
  }
}
```

### Querying Tasks

#### By Status

```bash
# Get all approved tasks (ready to work on)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status approved

# Get completed tasks
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status completed

# Get suggested tasks (needing approval)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status suggested

# Get in-progress tasks
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status in-progress
```

#### By Priority

```bash
# Get high priority tasks
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-priority high

# Get urgent tasks
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-priority urgent

# Get normal priority tasks
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-priority normal
```

#### Specific Task Details

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task <taskId>
```

**Example:**
```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task error_1758946224547_lrnbb2b8w
```

### Creating Tasks

#### Basic Task Creation

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Add user authentication",
  "description": "Implement JWT-based authentication with login and logout endpoints",
  "type": "feature",
  "priority": "high"
}'
```

**Required Fields:**
- `title` - Clear, specific task title
- `description` - Detailed description with acceptance criteria
- `type` - One of: `feature`, `error`, `test`, `audit`

**Optional Fields:**
- `priority` - `urgent`, `high`, `normal` (default), `low`
- `business_value` - Why this task matters
- `estimated_effort` - Hours to complete (1-20)
- `dependencies` - Array of task IDs
- `parent_id` - Parent task ID for subtasks

#### Feature Task Example

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Implement user registration",
  "description": "Create registration form with email validation, password strength checking, and confirmation email",
  "type": "feature",
  "priority": "high",
  "business_value": "Enables new users to create accounts and access platform features",
  "estimated_effort": 8
}'
```

#### Error/Bug Task Example

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Fix login page redirect loop",
  "description": "Users get stuck in redirect loop when accessing /login after logout. Fix redirect logic in auth middleware.",
  "type": "error",
  "priority": "urgent"
}'
```

**Note:** Error tasks can be worked on immediately without approval!

#### Test Task Example

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Add unit tests for authentication service",
  "description": "Write comprehensive unit tests covering login, logout, token validation, and password reset flows",
  "type": "test",
  "priority": "normal",
  "parent_id": "feature_auth_system_id"
}'
```

### Updating Tasks

#### Change Task Status

```bash
# Mark task as in-progress
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "status": "in-progress"
}'

# Mark task as completed
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "status": "completed"
}'

# Approve a suggested task
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "status": "approved"
}'

# Block a task
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "status": "blocked",
  "blocked_reason": "Waiting for API endpoint implementation"
}'
```

#### Update Progress

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "progress_percentage": 50
}'
```

#### Assign to Agent

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "assigned_to": "claude-agent-001",
  "status": "in-progress"
}'
```

#### Update Multiple Fields

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "status": "in-progress",
  "assigned_to": "claude-agent-001",
  "progress_percentage": 25,
  "priority": "high"
}'
```

### Deleting Tasks

**Use with caution!** Deleted tasks cannot be recovered.

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" delete-task <taskId>
```

---

## Agent Operations

### Agent Initialization

Initialize or reinitialize an agent:

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" reinitialize <agentId>
```

**Example:**
```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" reinitialize claude-agent-001
```

### Viewing Agent Tasks

Get all tasks assigned to a specific agent:

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-agent-tasks <agentId>
```

**Example:**
```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-agent-tasks claude-agent-001
```

### Finding Available Tasks

Get tasks available for an agent to claim:

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-available-tasks <agentId>
```

**Returns:** Tasks that are:
- Status: `approved`
- Not assigned to another agent
- Dependencies met
- Match agent capabilities

---

## Stop Hook Integration

### Understanding Stop Hooks

Stop hooks trigger when Claude Code conversation ends. They enable continuous operation by checking for available work.

### Configured Stop Hook

**Location:** `.claude/settings.json`

```json
{
  "hooks": {
    "Stop": [{
      "type": "command",
      "command": "node \"./taskmanager-api.js\" --project-root \"$(pwd)\" get-task-stats",
      "timeout": 10000
    }]
  }
}
```

### Stop Hook Response Protocol

When stop hook triggers:

1. **Query TaskManager FIRST**:
   ```bash
   timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats
   timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status approved
   ```

2. **Choose Action**:
   - **Have work in progress?** → Complete it
   - **Approved tasks exist?** → Claim and work on highest priority
   - **No work remaining?** → Verify stop readiness or emergency stop

3. **Never sit idle** - Always take action when stop hook triggers

### Stop Authorization

Multi-step process to authorize stopping when all work complete:

#### Step 1: Verify Readiness

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" verify-stop-readiness <agentId>
```

**Checks:**
- All tasks completed or rejected
- No in-progress work remaining
- User request fulfilled

#### Step 2: Start Authorization

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" start-authorization <agentId>
```

**Returns:** Authorization key for validation steps.

#### Step 3: Validate Criteria (Sequential)

**MUST be done in order:**

```bash
# 1. Validate focused codebase (only user-requested features)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> focused-codebase

# 2. Validate security (zero vulnerabilities)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> security-validation

# 3. Validate linting (zero errors/warnings)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> linter-validation

# 4. Validate type checking
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> type-validation

# 5. Validate build
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> build-validation

# 6. Validate startup
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> start-validation

# 7. Validate tests
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> test-validation
```

#### Step 4: Complete Authorization

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" complete-authorization <AUTH_KEY>
```

### Emergency Stop

Use ONLY when stop hook triggers repeatedly with no work remaining:

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" emergency-stop <agentId> "Stop hook persisting with no work remaining"
```

---

## Command Reference

### Information Commands

| Command | Purpose | Usage |
|---------|---------|-------|
| `guide` | Get full documentation | `timeout 10s node ./taskmanager-api.js guide` |
| `methods` | List all commands | `timeout 10s node ./taskmanager-api.js methods` |
| `get-task-stats` | Project statistics | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats` |

### Task Query Commands

| Command | Purpose | Usage |
|---------|---------|-------|
| `get-tasks-by-status` | Query by status | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status approved` |
| `get-tasks-by-priority` | Query by priority | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-priority high` |
| `get-task` | Get specific task | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task <taskId>` |
| `get-available-tasks` | Tasks for agent | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-available-tasks <agentId>` |

### Task Management Commands

| Command | Purpose | Usage |
|---------|---------|-------|
| `create-task` | Create new task | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{...}'` |
| `update-task` | Update existing task | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{...}'` |
| `delete-task` | Delete task | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" delete-task <taskId>` |

### Agent Commands

| Command | Purpose | Usage |
|---------|---------|-------|
| `reinitialize` | Initialize agent | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" reinitialize <agentId>` |
| `get-agent-tasks` | Get agent's tasks | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-agent-tasks <agentId>` |

### Stop Authorization Commands

| Command | Purpose | Usage |
|---------|---------|-------|
| `verify-stop-readiness` | Check if ready | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" verify-stop-readiness <agentId>` |
| `start-authorization` | Begin process | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" start-authorization <agentId>` |
| `validate-criterion` | Validate step | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <key> <criterion>` |
| `complete-authorization` | Finish authorization | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" complete-authorization <key>` |
| `emergency-stop` | Emergency stop | `timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" emergency-stop <agentId> "reason"` |

---

## Troubleshooting

### Common Issues

#### "Module not found" Error

**Problem:** Node modules not installed.

**Solution:**
```bash
npm install
```

#### "Timeout" Error

**Problem:** Command taking too long.

**Solution:** Increase timeout or run in background:
```bash
# Increase timeout
timeout 30s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats

# Check for performance issues
LOG_LEVEL=debug timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats
```

#### "Invalid JSON" Error

**Problem:** Malformed JSON in command arguments.

**Solution:** Validate JSON before passing:
```bash
echo '{"title":"Test","type":"feature"}' | jq .
```

#### Tasks Not Showing

**Problem:** Wrong project root or TASKS.json not found.

**Solution:** Always use `--project-root "$(pwd)"`:
```bash
# Verify TASKS.json exists
ls -la TASKS.json

# Verify TaskManager finds it
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats
```

### Debug Mode

Enable detailed logging:

```bash
LOG_LEVEL=debug timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats
```

### Verifying Installation

```bash
# Check TaskManager responds
timeout 10s node ./taskmanager-api.js guide

# Check files exist
ls -la taskmanager-api.js TASKS.json .claude/settings.json lib/

# Test basic operation
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats
```

---

## Best Practices

### Task Creation

✅ **DO:**
- Write specific, actionable titles
- Include detailed descriptions
- Set appropriate priorities
- Define business value
- Estimate effort realistically

❌ **DON'T:**
- Create vague tasks
- Skip descriptions
- Make everything urgent
- Create duplicates

### Task Management

✅ **DO:**
- Update status in real-time
- Mark complete immediately when done
- Use proper status transitions
- Keep one task in-progress at a time

❌ **DON'T:**
- Skip status updates
- Batch completions
- Leave tasks in-progress indefinitely
- Work on multiple tasks simultaneously

### Stop Hook Integration

✅ **DO:**
- Query TaskManager BEFORE deciding
- Complete current work first
- Use emergency stop appropriately
- Follow validation sequence exactly

❌ **DON'T:**
- Ignore TaskManager
- Skip approved task checks
- Skip validation steps
- Use emergency stop prematurely

---

## Quick Reference Card

### Essential Commands

```bash
# Get help
timeout 10s node ./taskmanager-api.js guide

# Check status
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats

# Get work
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status approved

# Create task
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{"title":"...","type":"feature"}'

# Start work
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <id> '{"status":"in-progress"}'

# Complete work
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <id> '{"status":"completed"}'
```

### File Locations

- **Global:** `/Users/jeremyparker/infinite-continue-stop-hook/taskmanager-api.js`
- **Local:** `./taskmanager-api.js`
- **Tasks:** `./TASKS.json`
- **Settings:** `./.claude/settings.json`

---

## Additional Resources

- **[Quick Reference](QUICKSTART.md)** - Condensed command reference
- **[Examples](EXAMPLES.md)** - Real-world usage scenarios
- **[README](README.md)** - Full project documentation
- **[CLAUDE.md](CLAUDE.md)** - Claude Code integration

---

**Need Help?** Run `timeout 10s node ./taskmanager-api.js guide` for comprehensive documentation.
