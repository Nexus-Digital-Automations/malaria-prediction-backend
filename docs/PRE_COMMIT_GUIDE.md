# Pre-commit Hooks Guide

This project uses [pre-commit](https://pre-commit.com/) hooks to ensure code quality and maintain consistent standards before commits are made to the repository.

## What are Pre-commit Hooks?

Pre-commit hooks are scripts that run automatically before each commit to check for common issues, format code, and enforce quality standards. This helps catch problems early and maintains consistent code quality across the project.

## Hooks Configured

Our pre-commit configuration includes the following hooks:

### 1. Ruff Linter (`ruff`)
- **Purpose**: Fast Python linter and code quality checker
- **What it does**: Checks for code style violations, unused imports, syntax errors, and other quality issues
- **Auto-fixes**: Automatically fixes many issues when possible
- **Configuration**: Uses settings from `pyproject.toml`

### 2. Ruff Formatter (`ruff-format`)
- **Purpose**: Fast Python code formatter
- **What it does**: Formats Python code consistently according to project standards
- **Auto-fixes**: Automatically formats code to match style guidelines

### 3. MyPy Type Checker (`mypy`)
- **Purpose**: Static type checking for Python
- **What it does**: Validates type annotations and catches type-related errors
- **Scope**: Only checks files in `src/` directory
- **Configuration**: Uses settings from `pyproject.toml`

### 4. Bandit Security Linter (`bandit`)
- **Purpose**: Security vulnerability scanner for Python
- **What it does**: Scans code for common security issues and vulnerabilities
- **Scope**: Only checks files in `src/` directory
- **Configuration**: Uses settings from `pyproject.toml`

### 5. General Code Quality Hooks
- **Trailing whitespace removal**: Removes unnecessary whitespace at line ends
- **End-of-file fixer**: Ensures files end with a newline
- **Merge conflict checker**: Detects unresolved merge conflict markers
- **Python AST validator**: Ensures Python syntax is valid
- **JSON/YAML/TOML syntax validation**: Validates configuration file syntax

## Installation and Setup

Pre-commit hooks are automatically installed when you set up the development environment:

```bash
# Install development dependencies (includes pre-commit)
uv sync --group dev

# Install the pre-commit hooks
pre-commit install
```

## Using Pre-commit

### Automatic Execution
Pre-commit hooks run automatically on every `git commit`. If any hook fails:
1. The commit is blocked
2. Issues are reported with details
3. Auto-fixable issues are corrected automatically
4. You need to review changes and commit again

### Manual Execution
You can run hooks manually at any time:

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run all hooks on staged files only
pre-commit run

# Run a specific hook on all files
pre-commit run ruff --all-files

# Run hooks on specific files
pre-commit run --files src/malaria_predictor/config.py
```

### Skipping Hooks (Use Sparingly)
In rare cases, you may need to skip hooks:

```bash
# Skip all pre-commit hooks (not recommended)
git commit --no-verify

# Skip specific checks by fixing the code instead (recommended)
```

## Common Scenarios

### Scenario 1: Linting Errors
```bash
$ git commit -m "Add new feature"
ruff-linter..............................................................Failed
- hook id: ruff
- exit code: 1

src/malaria_predictor/models.py:15:1: F401 'unused_import' imported but never used
```

**Solution**: Remove the unused import or add `# noqa: F401` if needed, then commit again.

### Scenario 2: Formatting Changes
```bash
$ git commit -m "Add new feature"
ruff-formatter...........................................................Failed
- hook id: ruff-format
- files were modified by this hook

5 files reformatted
```

**Solution**: Review the formatting changes and commit again. The files have been automatically formatted.

### Scenario 3: Type Checking Errors
```bash
$ git commit -m "Add new feature"
mypy-type-check..........................................................Failed
- hook id: mypy
- exit code: 1

src/malaria_predictor/models.py:20: error: Function is missing a return type annotation
```

**Solution**: Add proper type annotations to resolve the type checking errors.

### Scenario 4: Security Issues
```bash
$ git commit -m "Add new feature"
bandit-security-check....................................................Failed
- hook id: bandit
- exit code: 1

>> Issue: [B105:hardcoded_password_string] Possible hardcoded password
```

**Solution**: Remove hardcoded secrets and use environment variables or secure configuration instead.

## Configuration Files

### `.pre-commit-config.yaml`
Main configuration file defining all hooks, their versions, and settings.

### `pyproject.toml`
Contains configuration for:
- `[tool.ruff]` - Ruff linter and formatter settings
- `[tool.mypy]` - MyPy type checker settings
- `[tool.bandit]` - Bandit security scanner settings

## Benefits

### For Developers
- **Immediate Feedback**: Catch issues before they reach the repository
- **Consistent Style**: Automatic code formatting ensures consistency
- **Learning Tool**: Helps developers learn best practices and common issues
- **Time Saving**: Prevents failed CI/CD builds due to quality issues

### For the Team
- **Code Quality**: Maintains high standards across all contributions
- **Security**: Automatically scans for common security vulnerabilities
- **Consistency**: Ensures all code follows the same style and quality standards
- **Reduced Review Time**: Fewer basic issues in pull requests

## Troubleshooting

### Hook Installation Issues
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Update hooks to latest versions
pre-commit autoupdate
```

### Performance Issues
```bash
# Run hooks on changed files only (faster)
pre-commit run

# Skip slow hooks during development (commit with --no-verify, then run manually)
pre-commit run --all-files
```

### Configuration Updates
When configuration files change:
```bash
# Clean and reinstall hook environments
pre-commit clean
pre-commit install --install-hooks
```

## Best Practices

1. **Run hooks locally**: Test `pre-commit run --all-files` before pushing
2. **Fix issues promptly**: Don't accumulate linting errors
3. **Understand failures**: Learn from hook failures rather than bypassing them
4. **Keep hooks updated**: Regularly run `pre-commit autoupdate`
5. **Document exceptions**: If you must skip a hook, document why in commit message

## CI/CD Integration

Pre-commit hooks are also configured to run in our CI/CD pipeline as a backup, ensuring that even if hooks are bypassed locally, quality standards are maintained.

The configuration includes `pre-commit.ci` settings for automatic updates and fixes in pull requests.
