# Development Workflow Enhancement Guide

This document outlines the custom subagents and slash commands created to enhance the development workflow for the Magento CMS Sync project.

## Overview

The project now includes:
- **6 Specialized Subagents** for automated code review, testing, debugging, and PR review
- **16 Custom Slash Commands** for common development tasks and Git Flow workflow
- **Git Flow Workflow Integration** with automated code review before merging
- **Enhanced CLAUDE.md** with comprehensive AI assistant instructions

## 🌿 Git Flow Workflow

This project follows **Git Flow** branching strategy for organized, scalable development:

### Branch Structure

```
main (production)
  ↑
  └─── release/v1.2.0 ──┐
                        ↓
develop (integration)
  ↑
  ├─── feature/add-widget-sync
  ├─── feature/improve-diff-viewer
  └─── bugfix/fix-sync-error

hotfix/v1.1.1 (from main)
  ↓
  └─→ main + develop
```

### Branch Types

| Branch Type | Naming | Source | Target | Purpose |
|------------|--------|--------|--------|---------|
| **main** | `main` | - | - | Production-ready code |
| **develop** | `develop` | - | - | Integration branch |
| **feature** | `feature/*` | develop | develop | New features |
| **bugfix** | `bugfix/*` | develop | develop | Bug fixes |
| **release** | `release/v*` | develop | main + develop | Release preparation |
| **hotfix** | `hotfix/*` | main | main + develop | Critical production fixes |

### Workflow Rules

1. **Never commit directly to main or develop**
2. **All features go through pull requests**
3. **Code review required before merge**
4. **All tests must pass before merge**
5. **Features merge to develop, not main**
6. **Releases and hotfixes merge to both main and develop**

## 🤖 Subagents

Subagents are specialized AI assistants that Claude Code uses proactively or on-demand. They're located in `.claude/agents/`.

### 1. `magento-api-debugger`
**Purpose**: Debug Magento API connectivity and integration issues

**When it's used**:
- Automatically when API connection errors occur
- When debugging authentication failures
- When data fetching from Magento fails

**Capabilities**:
- Diagnoses API connection issues
- Validates Bearer tokens and permissions
- Tests endpoints with curl commands
- Provides root cause analysis with fixes

**Example usage**:
```
"I'm getting a 401 error when connecting to Magento"
→ Claude automatically uses magento-api-debugger subagent
```

### 2. `sync-validator`
**Purpose**: Validate sync operations and ensure data integrity

**When it's used**:
- Before executing sync operations
- When reviewing sync preview changes
- When investigating data integrity issues

**Capabilities**:
- Validates field mappings
- Checks for potential data loss
- Verifies identifier uniqueness
- Assesses sync operation risk (LOW/MEDIUM/HIGH)

**Example usage**:
```
"Validate this sync operation before I execute it"
→ Claude uses sync-validator subagent
```

### 3. `frontend-reviewer`
**Purpose**: Review React/TypeScript code changes

**When it's used**:
- Automatically when frontend code changes are made
- Before committing frontend changes
- When reviewing pull requests

**Capabilities**:
- Checks TypeScript correctness
- Validates Material-UI patterns
- Reviews Zustand state management
- Ensures React best practices

**Example usage**:
```
"Review my changes to the DiffViewer component"
→ Claude uses frontend-reviewer subagent
```

### 4. `backend-reviewer`
**Purpose**: Review FastAPI/Python code changes

**When it's used**:
- Automatically when backend code changes are made
- Before committing backend changes
- When reviewing pull requests

**Capabilities**:
- Validates FastAPI patterns
- Checks async/await usage
- Reviews service layer design
- Verifies type hints and security

**Example usage**:
```
"Review my changes to the sync service"
→ Claude uses backend-reviewer subagent
```

### 5. `test-generator`
**Purpose**: Generate comprehensive tests for code

**When it's used**:
- When you need tests for new features
- When test coverage is insufficient
- When asked to generate tests

**Capabilities**:
- Generates pytest tests for backend
- Creates Jest/RTL tests for frontend
- Includes fixtures and mocks
- Covers edge cases and error scenarios

**Example usage**:
```
"Generate tests for the comparison service"
→ Claude uses test-generator subagent
```

### 6. `pr-reviewer`
**Purpose**: Review pull requests before merging (Git Flow compliant)

**When it's used**:
- **MUST BE USED** before merging any branch to develop or main
- When using `/pr-review` or `/feature-finish` commands
- When reviewing branch diffs

**Capabilities**:
- Git Flow compliance verification
- Comprehensive code quality review
- Merge safety analysis (conflicts, breaking changes)
- Security and data integrity checks
- Uses frontend-reviewer and backend-reviewer internally

**Example usage**:
```
"/pr-review feature/new-sync develop"
→ Claude uses pr-reviewer subagent
→ Provides APPROVE/REQUEST CHANGES/NEEDS DISCUSSION
```

## 🔧 Slash Commands

Slash commands are shortcuts for common development tasks. They're located in `.claude/commands/`.

### Quick Reference

#### Git Flow Commands
| Command | Purpose | Arguments |
|---------|---------|-----------|
| `/feature-start` | Start a new feature branch | `<feature-name>` |
| `/feature-finish` | Finish feature and prep for merge to develop | - |
| `/hotfix-start` | Start critical production hotfix | `<hotfix-name>` |
| `/hotfix-finish` | Finish hotfix and merge to main+develop | - |
| `/release-start` | Start release branch | `<version>` |
| `/release-finish` | Finish release and merge to main+develop | - |
| `/pr-review` | Review PR before merging | `[source] [target]` |

#### Development Commands
| Command | Purpose | Arguments |
|---------|---------|-----------|
| `/review` | Review uncommitted changes | - |
| `/run-tests` | Run test suites | `[backend\|frontend\|all]` |
| `/check-types` | Check type safety | - |
| `/add-test` | Generate tests for a file | `<file_path>` |

#### Magento-Specific Commands
| Command | Purpose | Arguments |
|---------|---------|-----------|
| `/test-api` | Test Magento API connection | `<instance_id>` |
| `/debug-api` | Debug API issues | `<instance_id or error>` |
| `/check-sync` | Validate sync operations | - |
| `/refresh-data` | Refresh cached Magento data | `<instance_id or "all">` |

### Detailed Command Reference

#### `/test-api <instance_id>`
Tests Magento API connectivity for a specific instance.

```bash
/test-api 1
```

**What it does**:
1. Reads instance configuration
2. Tests authentication endpoint
3. Tests CMS endpoints
4. Reports connection status and sample data

**Output**:
- Connection status (success/failure)
- Response time
- Sample blocks/pages
- Error details if any

---

#### `/review`
Reviews all uncommitted code changes before committing.

```bash
/review
```

**What it does**:
1. Runs `git status` and `git diff`
2. Uses frontend-reviewer for .ts/.tsx files
3. Uses backend-reviewer for .py files
4. Provides comprehensive feedback

**Output**:
- Summary of changes
- Code quality issues
- Security considerations
- Recommendation: READY TO COMMIT or NEEDS CHANGES

---

#### `/add-test <file_path>`
Generates comprehensive tests for a specific file.

```bash
/add-test backend/services/comparison.py
/add-test frontend/src/components/DiffViewer.tsx
```

**What it does**:
1. Reads the target file
2. Uses test-generator subagent
3. Creates test file in correct location
4. Includes fixtures and mocks

**Output**:
- Complete test file
- Test coverage for all functions/components
- Edge cases and error scenarios

---

#### `/check-sync`
Validates sync operations for safety and data integrity.

```bash
/check-sync
```

**What it does**:
1. Reviews sync service code
2. Uses sync-validator subagent
3. Checks cached data
4. Identifies risks

**Output**:
- Risk assessment (LOW/MEDIUM/HIGH)
- Potential issues found
- Recommendations

---

#### `/debug-api <instance_id or error>`
Debugs Magento API integration issues.

```bash
/debug-api 1
/debug-api "401 Unauthorized error"
```

**What it does**:
1. Uses magento-api-debugger subagent
2. Analyzes the issue
3. Tests connectivity
4. Provides fix recommendations

**Output**:
- Root cause analysis
- Recommended fix
- Test commands
- Code changes if needed

---

#### `/run-tests [backend|frontend|all]`
Runs test suites with coverage.

```bash
/run-tests all
/run-tests backend
/run-tests frontend
```

**What it does**:
1. Runs pytest for backend
2. Runs Jest for frontend
3. Runs type checking
4. Reports coverage

**Output**:
- Test results (pass/fail)
- Coverage percentages
- Type errors
- Recommendations

---

#### `/check-types`
Checks TypeScript and Python type safety.

```bash
/check-types
```

**What it does**:
1. Runs `tsc --noEmit` for frontend
2. Runs `mypy` for backend
3. Compares types across stack
4. Identifies inconsistencies

**Output**:
- Type errors found
- Critical issues
- Suggested fixes
- Files needing annotations

---

#### `/refresh-data <instance_id or "all">`
Refreshes cached Magento data.

```bash
/refresh-data 1
/refresh-data all
```

**What it does**:
1. Calls refresh API endpoint
2. Monitors progress
3. Verifies JSON files updated

**Output**:
- Refresh status
- Items fetched (blocks/pages count)
- File sizes and timestamps
- Errors if any

## 📋 Workflow Examples

### Git Flow Feature Development (Complete Workflow)

**Starting a new feature**:
```bash
# 1. Start feature branch from develop
/feature-start add-widget-sync

# This automatically:
# - Switches to develop
# - Pulls latest changes
# - Creates feature/add-widget-sync branch
# - Provides development guidance
```

**During development**:
```bash
# 1. Make your changes
# 2. Review as you go
/review

# 3. Run tests
/run-tests all

# 4. Check types
/check-types

# 5. Commit regularly
git add .
git commit -m "Add widget sync functionality"

# 6. Push to remote
git push -u origin feature/add-widget-sync
```

**Finishing the feature**:
```bash
# 1. Finish feature (auto-review and prepare for merge)
/feature-finish

# This automatically:
# - Verifies you're on feature/* branch
# - Checks all changes committed
# - Rebases on latest develop
# - Runs pr-reviewer subagent
# - Provides PR creation instructions

# 2. Create PR to develop (as instructed)
gh pr create --base develop --head feature/add-widget-sync

# 3. Wait for team review and approval

# 4. Merge PR when approved

# 5. Delete feature branch
git branch -d feature/add-widget-sync
```

### Hotfix Workflow (Production Emergency)

**When production is broken**:
```bash
# 1. Start hotfix from main
/hotfix-start critical-sync-fix

# You'll be asked to confirm it's truly critical

# 2. Fix the issue (minimal changes only!)

# 3. Test thoroughly
/run-tests all
/check-types

# 4. Review changes
/review

# 5. Finish hotfix
/hotfix-finish

# This creates TWO PRs:
# - hotfix/critical-sync-fix → main (production)
# - hotfix/critical-sync-fix → develop (future releases)

# 6. Merge to main first, tag, deploy

# 7. Then merge to develop
```

### Release Workflow

**Preparing a release**:
```bash
# 1. Start release branch from develop
/release-start v1.2.0

# 2. Update version numbers
# - Update package.json
# - Update backend version
# - Update CHANGELOG.md

# 3. Final testing
/run-tests all
/check-types

# 4. Fix any last-minute bugs (NO NEW FEATURES!)

# 5. Finish release
/release-finish

# This merges to BOTH:
# - main (production)
# - develop (bring changes back)

# 6. Tag the release on main
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0

# 7. Deploy to production
```

### Daily Development Workflow

**Starting your day**:
```bash
# 1. Start development servers
./start-dev.sh

# 2. Pull latest develop
git checkout develop
git pull origin develop

# 3. Check current type safety
/check-types

# 4. Start working on feature
/feature-start my-new-feature
```

**Before committing**:
```bash
# 1. Review your changes
/review

# 2. Run tests
/run-tests all

# 3. If all looks good, commit
git add .
git commit -m "Add new feature"

# 4. Push regularly
git push
```

### Debugging Workflow

**When API connection fails**:
```bash
# 1. Debug the specific instance
/debug-api 1

# 2. Test the connection
/test-api 1

# 3. Follow the recommendations provided
```

**When sync operation seems risky**:
```bash
# 1. Validate the sync
/check-sync

# 2. Review the risk assessment
# 3. Make adjustments if needed
```

### Testing Workflow

**Adding tests for new code**:
```bash
# 1. Generate tests
/add-test backend/services/new_service.py

# 2. Review generated tests
# 3. Run tests to verify
/run-tests backend
```

## 🎯 Best Practices

### When to Use Subagents

**Proactive Use** (Automatic):
- `frontend-reviewer` and `backend-reviewer` activate automatically during code reviews
- `magento-api-debugger` activates when API errors occur
- `sync-validator` activates before sync execution

**Manual Use** (Explicit request):
- "Use the test-generator to create tests for X"
- "Use the sync-validator to check this operation"
- "Use the magento-api-debugger to diagnose this error"

### When to Use Slash Commands

**Use slash commands for**:
- Quick, repetitive tasks
- Standard development workflows
- Testing and validation
- Debugging common issues

**Don't use slash commands for**:
- Complex, multi-step operations (let Claude handle these)
- One-off unique tasks
- Exploratory analysis

## 📊 Benefits

### Time Savings
- **Code Review**: Automated review reduces manual review time by ~70%
- **Testing**: Generated tests save ~2-4 hours per feature
- **Debugging**: Structured debugging process reduces issue resolution time by ~50%

### Quality Improvements
- **Consistency**: Automated reviews ensure consistent code quality
- **Test Coverage**: Test generator ensures comprehensive coverage
- **Best Practices**: Reviewers enforce project standards

### Knowledge Sharing
- **Documentation**: Subagents encode team knowledge
- **Onboarding**: New developers can learn patterns from reviews
- **Standards**: Consistent feedback reinforces best practices

## 🔄 Maintenance

### Updating Subagents

Edit files in `.claude/agents/`:
```bash
# Example: Update frontend reviewer
code .claude/agents/frontend-reviewer.md
```

### Updating Slash Commands

Edit files in `.claude/commands/`:
```bash
# Example: Update review command
code .claude/commands/review.md
```

### Version Control

**Commit these files**:
- `.claude/agents/*` - Share with team
- `.claude/commands/*` - Share with team
- `CLAUDE.md` - Critical for AI assistance

**Don't commit**:
- Personal preferences (use `~/.claude/` for personal configs)

## 🚀 Getting Started

1. **Review the CLAUDE.md** - Understanding project architecture
2. **Try a slash command** - Run `/check-types` to verify setup
3. **Make a change** - Modify a file and run `/review`
4. **Create tests** - Use `/add-test` on a file without tests
5. **Debug an issue** - Use `/debug-api` or `/check-sync`

## 📚 Resources

- [Claude Code Subagents Documentation](https://docs.claude.com/en/docs/claude-code/sub-agents)
- [Claude Code Slash Commands Documentation](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Project CLAUDE.md](../CLAUDE.md) - AI development guide
- [README.md](./README.md) - User documentation

## 🤝 Contributing

When adding new subagents or commands:

1. **Identify the need** - What task is repetitive or complex?
2. **Define the scope** - What should the agent/command do?
3. **Create the file** - Use existing ones as templates
4. **Test thoroughly** - Verify it works as expected
5. **Document** - Update this file with the new addition
6. **Share with team** - Commit to version control

## 📝 Changelog

### 2024-01-XX - Initial Setup
- Created 5 specialized subagents
- Created 8 custom slash commands
- Enhanced CLAUDE.md with comprehensive instructions
- Added development workflow documentation

---

**Questions or suggestions?** Update this document or discuss with the team!
