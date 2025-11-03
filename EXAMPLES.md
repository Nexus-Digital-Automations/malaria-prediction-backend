# TaskManager Real-World Examples

Practical examples of using TaskManager for common development scenarios.

## Table of Contents

- [Single Feature Development](#single-feature-development)
- [Bug Fixing Workflow](#bug-fixing-workflow)
- [Multi-Task Epic](#multi-task-epic)
- [Test-Driven Development](#test-driven-development)
- [Emergency Production Issue](#emergency-production-issue)
- [Refactoring Project](#refactoring-project)
- [Multi-Agent Coordination](#multi-agent-coordination)
- [Daily Development Workflow](#daily-development-workflow)

---

## Single Feature Development

### Scenario: Add User Profile Page

**Goal:** Implement a user profile page with edit functionality.

#### Step 1: Create the Feature Task

```bash
# Create main feature task
TASK_ID=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Implement user profile page",
  "description": "Create profile page showing user information with edit capability. Include profile picture upload, bio text, and account settings.",
  "type": "feature",
  "priority": "high",
  "business_value": "Allows users to customize their profiles and manage account information",
  "estimated_effort": 8
}' | jq -r '.task.id')

echo "Created task: $TASK_ID"
```

#### Step 2: Approve the Task (if status is 'suggested')

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "status": "approved"
}'
```

#### Step 3: Start Working

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "status": "in-progress",
  "assigned_to": "claude-dev-001"
}'
```

#### Step 4: Update Progress

```bash
# After creating profile component
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "progress_percentage": 33
}'

# After implementing edit functionality
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "progress_percentage": 66
}'

# After adding profile picture upload
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "progress_percentage": 100
}'
```

#### Step 5: Mark Complete

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "status": "completed"
}'
```

---

## Bug Fixing Workflow

### Scenario: Fix Critical Login Bug

**Goal:** Resolve urgent production login issue.

#### Step 1: Create Error Task (Can Work Immediately!)

```bash
# Error tasks don't need approval - start working right away
TASK_ID=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "FIX: Login redirects to 404 after successful authentication",
  "description": "Users successfully authenticate but are redirected to /404 instead of dashboard. Issue appears to be in AuthRedirect middleware. Error started after deployment v2.3.1.",
  "type": "error",
  "priority": "urgent"
}' | jq -r '.task.id')

echo "Created error task: $TASK_ID"
```

#### Step 2: Immediately Start Work (No Approval Needed)

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "status": "in-progress",
  "assigned_to": "claude-dev-001"
}'
```

#### Step 3: Fix the Bug

```bash
# After identifying the issue
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "progress_percentage": 50
}'

# After implementing fix
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "progress_percentage": 80
}'

# After testing fix
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "progress_percentage": 100
}'
```

#### Step 4: Mark Complete

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "status": "completed"
}'
```

---

## Multi-Task Epic

### Scenario: Build Complete Authentication System

**Goal:** Implement full auth system with multiple related tasks.

#### Step 1: Create Parent Epic Task

```bash
PARENT_ID=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "EPIC: Complete Authentication System",
  "description": "Build comprehensive authentication system with JWT tokens, OAuth providers, password reset, and email verification",
  "type": "feature",
  "priority": "high",
  "business_value": "Essential for platform security and user management",
  "estimated_effort": 40
}' | jq -r '.task.id')

echo "Created epic: $PARENT_ID"
```

#### Step 2: Create Subtasks

```bash
# Subtask 1: JWT Implementation
TASK_1=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Implement JWT token authentication",
  "description": "Create JWT token generation, validation, and refresh logic",
  "type": "feature",
  "priority": "high",
  "parent_id": "'$PARENT_ID'",
  "estimated_effort": 8
}' | jq -r '.task.id')

# Subtask 2: Login/Logout
TASK_2=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Build login and logout endpoints",
  "description": "Create /api/login and /api/logout with proper token handling",
  "type": "feature",
  "priority": "high",
  "parent_id": "'$PARENT_ID'",
  "dependencies": ["'$TASK_1'"],
  "estimated_effort": 6
}' | jq -r '.task.id')

# Subtask 3: Password Reset
TASK_3=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Implement password reset flow",
  "description": "Email-based password reset with secure tokens and expiration",
  "type": "feature",
  "priority": "normal",
  "parent_id": "'$PARENT_ID'",
  "estimated_effort": 10
}' | jq -r '.task.id')

# Subtask 4: OAuth Integration
TASK_4=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Add Google and GitHub OAuth",
  "description": "Integrate OAuth2 login for Google and GitHub providers",
  "type": "feature",
  "priority": "normal",
  "parent_id": "'$PARENT_ID'",
  "dependencies": ["'$TASK_1'"],
  "estimated_effort": 12
}' | jq -r '.task.id')

# Subtask 5: Tests
TASK_5=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Write comprehensive auth tests",
  "description": "Unit and integration tests for entire auth system",
  "type": "test",
  "priority": "high",
  "parent_id": "'$PARENT_ID'",
  "dependencies": ["'$TASK_2'", "'$TASK_3'", "'$TASK_4'"],
  "estimated_effort": 8
}' | jq -r '.task.id')
```

#### Step 3: Approve All Tasks

```bash
# Approve all subtasks
for task in $TASK_1 $TASK_2 $TASK_3 $TASK_4 $TASK_5; do
  timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $task '{
    "status": "approved"
  }'
done
```

#### Step 4: Work Through in Order (Respecting Dependencies)

```bash
# Work on Task 1 first (no dependencies)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_1 '{"status":"in-progress"}'
# ... implement JWT ...
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_1 '{"status":"completed"}'

# Now Task 2 and Task 4 can start (dependency met)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_2 '{"status":"in-progress"}'
# ... implement login/logout ...
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_2 '{"status":"completed"}'

# Continue with remaining tasks...
```

---

## Test-Driven Development

### Scenario: TDD for New Feature

**Goal:** Implement feature using test-first approach.

#### Step 1: Create Test Task First

```bash
TEST_TASK=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Write tests for shopping cart functionality",
  "description": "Create test suite for cart: add item, remove item, update quantity, calculate total, apply discounts",
  "type": "test",
  "priority": "high",
  "estimated_effort": 6
}' | jq -r '.task.id')
```

#### Step 2: Create Feature Implementation Task (Dependent on Tests)

```bash
FEATURE_TASK=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Implement shopping cart functionality",
  "description": "Build shopping cart with add, remove, update, and calculation features to pass all tests",
  "type": "feature",
  "priority": "high",
  "dependencies": ["'$TEST_TASK'"],
  "estimated_effort": 12
}' | jq -r '.task.id')
```

#### Step 3: Approve and Work Test-First

```bash
# Approve test task
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TEST_TASK '{"status":"approved"}'

# Write tests first
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TEST_TASK '{"status":"in-progress"}'
# ... write failing tests ...
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TEST_TASK '{"status":"completed"}'

# Now implement feature to make tests pass
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $FEATURE_TASK '{"status":"approved"}'
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $FEATURE_TASK '{"status":"in-progress"}'
# ... implement until tests pass ...
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $FEATURE_TASK '{"status":"completed"}'
```

---

## Emergency Production Issue

### Scenario: Site Down - Database Connection Errors

**Goal:** Resolve critical production outage immediately.

#### Step 1: Create Urgent Error Task

```bash
EMERGENCY_TASK=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "URGENT: Production database connection pool exhausted",
  "description": "Site is down. Database connection pool hitting max connections (100/100). Users seeing 500 errors. Logs show connection leaks in user service. IMMEDIATE ACTION REQUIRED.",
  "type": "error",
  "priority": "urgent"
}' | jq -r '.task.id')
```

#### Step 2: Immediately Claim and Start

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $EMERGENCY_TASK '{
  "status": "in-progress",
  "assigned_to": "on-call-agent"
}'
```

#### Step 3: Document Progress

```bash
# After identifying leak
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $EMERGENCY_TASK '{
  "progress_percentage": 40
}'

# After implementing fix
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $EMERGENCY_TASK '{
  "progress_percentage": 70
}'

# After deploying hotfix
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $EMERGENCY_TASK '{
  "progress_percentage": 100
}'
```

#### Step 4: Mark Complete and Create Follow-Up

```bash
# Mark emergency resolved
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $EMERGENCY_TASK '{
  "status": "completed"
}'

# Create follow-up tasks for root cause
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Add connection pool monitoring",
  "description": "Implement alerts for connection pool usage >80%",
  "type": "feature",
  "priority": "high",
  "parent_id": "'$EMERGENCY_TASK'"
}'

timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Audit all database queries for connection leaks",
  "description": "Review all services for proper connection disposal",
  "type": "audit",
  "priority": "high",
  "parent_id": "'$EMERGENCY_TASK'"
}'
```

---

## Refactoring Project

### Scenario: Refactor Legacy Code Module

**Goal:** Clean up and modernize old authentication module.

#### Step 1: Create Audit Task for Assessment

```bash
AUDIT_TASK=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Audit legacy auth module for refactoring",
  "description": "Analyze lib/auth-legacy.js to identify technical debt, security issues, and refactoring opportunities. Document findings.",
  "type": "audit",
  "priority": "normal",
  "estimated_effort": 4
}' | jq -r '.task.id')
```

#### Step 2: Create Refactoring Tasks Based on Audit

```bash
# Approve and complete audit first
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $AUDIT_TASK '{"status":"approved"}'
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $AUDIT_TASK '{"status":"in-progress"}'
# ... perform audit ...
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $AUDIT_TASK '{"status":"completed"}'

# Now create specific refactoring tasks
REFACTOR_1=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Replace callbacks with async/await in auth module",
  "description": "Modernize callback-based code to use async/await patterns",
  "type": "feature",
  "priority": "normal",
  "parent_id": "'$AUDIT_TASK'",
  "estimated_effort": 8
}' | jq -r '.task.id')

REFACTOR_2=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Extract auth business logic from controllers",
  "description": "Move auth logic to dedicated service layer following clean architecture",
  "type": "feature",
  "priority": "normal",
  "parent_id": "'$AUDIT_TASK'",
  "dependencies": ["'$REFACTOR_1'"],
  "estimated_effort": 12
}' | jq -r '.task.id')

REFACTOR_3=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Add comprehensive tests for refactored auth",
  "description": "Create test suite with >90% coverage for new auth implementation",
  "type": "test",
  "priority": "high",
  "parent_id": "'$AUDIT_TASK'",
  "dependencies": ["'$REFACTOR_2'"],
  "estimated_effort": 10
}' | jq -r '.task.id')
```

---

## Multi-Agent Coordination

### Scenario: Multiple Agents Working Simultaneously

**Goal:** Coordinate 3 agents working on different parts of a feature.

#### Step 1: Create Tasks for Each Agent

```bash
# Frontend task
FRONTEND_TASK=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Build dashboard UI components",
  "description": "Create React components for dashboard: widgets, charts, filters",
  "type": "feature",
  "priority": "high",
  "required_capabilities": ["frontend"],
  "estimated_effort": 12
}' | jq -r '.task.id')

# Backend task
BACKEND_TASK=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Implement dashboard API endpoints",
  "description": "Create REST API for dashboard data: /api/dashboard/stats, /api/dashboard/charts",
  "type": "feature",
  "priority": "high",
  "required_capabilities": ["backend"],
  "estimated_effort": 10
}' | jq -r '.task.id')

# Database task
DATABASE_TASK=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Optimize dashboard queries",
  "description": "Create materialized views and indexes for fast dashboard queries",
  "type": "feature",
  "priority": "high",
  "required_capabilities": ["database"],
  "estimated_effort": 8
}' | jq -r '.task.id')
```

#### Step 2: Approve All Tasks

```bash
for task in $FRONTEND_TASK $BACKEND_TASK $DATABASE_TASK; do
  timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $task '{
    "status": "approved"
  }'
done
```

#### Step 3: Each Agent Claims Their Task

```bash
# Agent 1 (Frontend specialist)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $FRONTEND_TASK '{
  "status": "in-progress",
  "assigned_to": "frontend-agent-001"
}'

# Agent 2 (Backend specialist)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $BACKEND_TASK '{
  "status": "in-progress",
  "assigned_to": "backend-agent-001"
}'

# Agent 3 (Database specialist)
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $DATABASE_TASK '{
  "status": "in-progress",
  "assigned_to": "database-agent-001"
}'
```

#### Step 4: Monitor Progress Across Agents

```bash
# Check overall status
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats

# Check specific agent progress
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-agent-tasks frontend-agent-001
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-agent-tasks backend-agent-001
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-agent-tasks database-agent-001
```

---

## Daily Development Workflow

### Scenario: Typical Development Day

**Goal:** Manage full day of varied development tasks.

#### Morning: Check Status and Plan Day

```bash
# Check what's pending
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats

# See approved high-priority work
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-priority high | jq '.tasks[] | {id: .id, title: .title, status: .status}'

# Check yesterday's in-progress tasks
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status in-progress
```

#### Mid-Morning: Fix Bug Reported by User

```bash
# Create and immediately start error task
BUG_ID=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Fix profile image upload failing for PNG files",
  "description": "Users cannot upload PNG profile images - only JPG works. Error in image validation logic.",
  "type": "error",
  "priority": "high"
}' | jq -r '.task.id')

timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $BUG_ID '{"status":"in-progress"}'
# ... fix bug ...
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $BUG_ID '{"status":"completed"}'
```

#### Afternoon: Continue Feature Work

```bash
# Get your in-progress feature
FEATURE_ID=$(timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-agent-tasks my-agent-id | jq -r '.tasks[] | select(.type=="feature" and .status=="in-progress") | .id')

# Update progress
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $FEATURE_ID '{
  "progress_percentage": 75
}'

# Complete feature
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $FEATURE_ID '{
  "status": "completed",
  "progress_percentage": 100
}'
```

#### End of Day: Check Completion and Plan Tomorrow

```bash
# See what was accomplished today
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status completed | jq '.tasks[-5:]'

# Check what's queued for tomorrow
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-tasks-by-status approved

# Check completion rate
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" get-task-stats | jq '.statistics.completion_rate'
```

---

## Tips for Effective TaskManager Use

### 1. Use Descriptive Titles

✅ **Good:** "Fix authentication timeout in production login flow"
❌ **Bad:** "Fix bug"

### 2. Include Acceptance Criteria in Descriptions

```bash
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Add email notifications",
  "description": "Implement email notifications with following criteria: 1) Send on new message, 2) Include unsubscribe link, 3) Support HTML and plain text, 4) Rate limit to 1 per hour max, 5) Include user preferences",
  "type": "feature"
}'
```

### 3. Update Progress Regularly

```bash
# After each major milestone
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "progress_percentage": 25  # Database schema done
}'
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "progress_percentage": 50  # API endpoints complete
}'
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "progress_percentage": 75  # Frontend integration done
}'
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" update-task $TASK_ID '{
  "progress_percentage": 100  # Tests passing
}'
```

### 4. Use Dependencies for Logical Ordering

```bash
# Task B depends on Task A
timeout 10s node ./taskmanager-api.js --project-root "$(pwd)" create-task '{
  "title": "Task B",
  "dependencies": ["task-a-id"],
  ...
}'
```

### 5. Set Appropriate Priorities

- **`urgent`**: Production down, security vulnerability, data loss
- **`high`**: User-impacting bugs, important features, blocking issues
- **`normal`**: Regular features, improvements, non-critical bugs
- **`low`**: Nice-to-haves, cosmetic changes, future enhancements

---

## Additional Resources

- **[Usage Guide](TASKMANAGER-USAGE.md)** - Complete documentation
- **[Quick Reference](QUICKSTART.md)** - Command cheat sheet
- **[README](README.md)** - Project overview

---

**Got questions?** Run `timeout 10s node ./taskmanager-api.js guide` for comprehensive help.
