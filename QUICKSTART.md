# TaskManager Quick Reference

Quick reference guide for common TaskManager operations. For detailed documentation, see [TASKMANAGER-USAGE.md](TASKMANAGER-USAGE.md).

## Essential Commands

### Get Help

```bash
# Full documentation
timeout 10s node ./taskmanager-api.js guide

# List all commands
timeout 10s node ./taskmanager-api.js methods
```

### Check Project Status

```bash
# Get statistics
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats

# Get approved tasks (ready to work)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status approved

# Get high priority tasks
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-priority high
```

### Create Tasks

```bash
# Feature task
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Add user authentication",
  "description": "Implement JWT-based auth",
  "type": "feature",
  "priority": "high"
}'

# Error/Bug task (can work immediately - no approval needed)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Fix login redirect loop",
  "description": "Users stuck in redirect",
  "type": "error",
  "priority": "urgent"
}'

# Test task
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Add auth service tests",
  "description": "Unit tests for login/logout",
  "type": "test"
}'
```

### Update Tasks

```bash
# Start working
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "status": "in-progress"
}'

# Update progress
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "progress_percentage": 50
}'

# Mark complete
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "status": "completed"
}'

# Approve suggested task
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "status": "approved"
}'

# Block task
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{
  "status": "blocked",
  "blocked_reason": "Waiting for API"
}'
```

### Query Tasks

```bash
# By status
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status approved
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status completed
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status suggested
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status in-progress

# By priority
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-priority urgent
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-priority high
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-priority normal

# Specific task
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task <taskId>

# Available for agent
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-available-tasks <agentId>
```

### Agent Operations

```bash
# Initialize agent
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" reinitialize <agentId>

# Get agent's tasks
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-agent-tasks <agentId>
```

### Stop Hook Response

```bash
# When stop hook triggers - ALWAYS query first
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status approved
```

### Stop Authorization (When All Work Complete)

```bash
# 1. Verify readiness
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" verify-stop-readiness <agentId>

# 2. Start authorization (returns AUTH_KEY)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" start-authorization <agentId>

# 3. Validate (sequential - must be in order)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> focused-codebase
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> security-validation
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> linter-validation
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> type-validation
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> build-validation
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> start-validation
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" validate-criterion <AUTH_KEY> test-validation

# 4. Complete authorization
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" complete-authorization <AUTH_KEY>
```

### Emergency Stop

```bash
# Only when stop hook persists with no work
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" emergency-stop <agentId> "Stop hook persisting with no work"
```

---

## Task Lifecycle

```
suggested → approved → in-progress → completed
     ↓           ↓            ↓
  rejected    blocked      failed
```

## Task Types

- **`feature`** - New functionality (requires approval)
- **`error`** - Bug fix (can work immediately!)
- **`test`** - Test creation/modification
- **`audit`** - Code review/quality check

## Priority Levels

- **`urgent`** - Critical, immediate action
- **`high`** - Important, prioritize
- **`normal`** - Standard (default)
- **`low`** - Nice to have

---

## Common Workflows

### Workflow 1: Complete a Feature Task

```bash
# 1. Find approved tasks
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status approved

# 2. Start work
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{"status":"in-progress"}'

# 3. Update progress periodically
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{"progress_percentage":50}'

# 4. Mark complete
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{"status":"completed"}'
```

### Workflow 2: Fix a Bug (No Approval Needed)

```bash
# 1. Create error task
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title":"Fix database connection timeout",
  "description":"Connection pool exhausted under load",
  "type":"error",
  "priority":"urgent"
}'

# 2. Start work immediately (error tasks don't need approval)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{"status":"in-progress"}'

# 3. Fix the bug...

# 4. Mark complete
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{"status":"completed"}'
```

### Workflow 3: Handle Stop Hook Trigger

```bash
# 1. MANDATORY: Query TaskManager first
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats

# 2. Check for approved work
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status approved

# 3a. If work exists: claim it
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task <taskId> '{"status":"in-progress"}'

# 3b. If no work: verify stop readiness
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" verify-stop-readiness <agentId>
```

---

## File Locations

### Global Installation
```
/Users/jeremyparker/infinite-continue-stop-hook/taskmanager-api.js
/Users/jeremyparker/infinite-continue-stop-hook/TASKS.json
/Users/jeremyparker/.claude/settings.json
```

### Project-Local Installation
```
./taskmanager-api.js
./TASKS.json
./.claude/settings.json
./lib/
```

---

## Troubleshooting Quick Fixes

### Module Not Found
```bash
npm install
```

### Timeout Errors
```bash
# Increase timeout
timeout 30s node ./taskmanager-api.js --project-root "$(pwd)" <command>

# Or enable debug mode
LOG_LEVEL=debug timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" <command>
```

### Invalid JSON
```bash
# Validate JSON first
echo '{"title":"Test"}' | jq .
```

### Tasks Not Showing
```bash
# Verify TASKS.json exists
ls -la TASKS.json

# Ensure using correct project root
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats
```

---

## Best Practices Checklist

✅ **DO:**
- Query TaskManager before deciding what to do
- Update task status in real-time
- Use appropriate task types
- Set realistic priorities
- Complete tasks immediately when done

❌ **DON'T:**
- Start work without checking TaskManager
- Skip status updates
- Make everything urgent
- Work on multiple tasks simultaneously
- Use emergency stop prematurely

---

## Stop Hook Protocol

**When stop hook triggers:**

1. ✅ Query TaskManager FIRST
2. ✅ Complete current work OR claim new work
3. ✅ NEVER sit idle
4. ✅ Use emergency stop only if hook persists with no work

**FORBIDDEN:**
- ❌ Ignoring TaskManager
- ❌ Asking "what should I do?"
- ❌ Sitting idle

---

## Additional Resources

- **[Full Documentation](TASKMANAGER-USAGE.md)** - Complete usage guide
- **[Examples](EXAMPLES.md)** - Real-world scenarios
- **[README](README.md)** - Project overview

---

**Quick Help:** `timeout 10s node ./taskmanager-api.js guide`
