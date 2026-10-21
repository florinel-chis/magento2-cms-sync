# Git Flow Integration - Complete Guide

## Overview

This project now implements **Git Flow** workflow with automated code review and merge safety checks. All features, releases, and hotfixes follow a structured branching strategy with mandatory code review before merging.

## 🌿 Git Flow Branch Structure

```
┌─────────────────────────────────────────────────────────────┐
│                      Git Flow Workflow                       │
└─────────────────────────────────────────────────────────────┘

main (production)           [v1.0.0]──────[v1.1.0]──────[v1.2.0]
  ↑                                ↑            ↑            ↑
  │                                │            │            │
  └──── hotfix/v1.0.1 ────────────┤            │            │
          (critical fix)            │            │            │
                                    │            │            │
                              release/v1.1.0    │      release/v1.2.0
                                    ↑            │            ↑
                                    │            │            │
develop (integration)       ────────┴────────────┴────────────┴────
  ↑  ↑  ↑                       ↑         ↑            ↑
  │  │  └── bugfix/fix-error ──┘         │            │
  │  └───── feature/widgets ─────────────┘            │
  └──────── feature/diff-viewer ──────────────────────┘
```

## Branch Types

| Branch | Naming | Source | Target | Purpose | Command |
|--------|--------|--------|--------|---------|---------|
| **main** | `main` | - | - | Production code | - |
| **develop** | `develop` | - | - | Integration | - |
| **feature** | `feature/*` | develop | develop | New features | `/feature-start` |
| **bugfix** | `bugfix/*` | develop | develop | Bug fixes | `/feature-start bugfix/*` |
| **release** | `release/v*` | develop | main + develop | Release prep | `/release-start` |
| **hotfix** | `hotfix/*` | main | main + develop | Production fixes | `/hotfix-start` |

## 🚨 Critical Rules

### ❌ NEVER Do This

1. **Never commit directly to `main` or `develop`**
2. **Never merge without code review** (use `/pr-review`)
3. **Never skip tests before merging**
4. **Never add features to release or hotfix branches**
5. **Never merge feature branches to main** (only to develop)

### ✅ ALWAYS Do This

1. **Always start features with** `/feature-start <name>`
2. **Always review before merge** with `/pr-review`
3. **Always run tests** with `/run-tests all`
4. **Always check types** with `/check-types`
5. **Always follow branch naming conventions**

## 📋 Complete Workflows

### Feature Development Workflow

```bash
# 1. Start new feature from develop
/feature-start add-category-sync

# This automatically:
# - Switches to develop
# - Pulls latest changes
# - Creates feature/add-category-sync branch
# - Provides guidance

# 2. Make your changes
# ... edit files ...

# 3. Review as you go
/review

# 4. Run tests
/run-tests all

# 5. Check types
/check-types

# 6. Commit regularly
git add .
git commit -m "Add category sync functionality"

# 7. Push to remote
git push -u origin feature/add-category-sync

# 8. Finish feature (triggers comprehensive review)
/feature-finish

# This automatically:
# - Checks you're on feature/* branch
# - Verifies all changes committed
# - Rebases on latest develop
# - Runs pr-reviewer subagent for comprehensive review
# - Checks Git Flow compliance
# - Verifies code quality
# - Ensures tests pass
# - Provides PR creation instructions

# 9. Create PR to develop (as instructed)
gh pr create --base develop --head feature/add-category-sync \
  --title "Add category sync functionality" \
  --body "Implements category synchronization feature"

# 10. Code Reviewer: Review the PR
/pr-review feature/add-category-sync develop

# This triggers pr-reviewer subagent which:
# - Verifies Git Flow compliance
# - Runs frontend-reviewer for .ts/.tsx files
# - Runs backend-reviewer for .py files
# - Checks for security issues
# - Verifies no merge conflicts
# - Ensures tests pass
# - Provides APPROVE/REQUEST CHANGES recommendation

# 11. Address feedback if needed
# ... make changes based on review ...
git add .
git commit -m "Address review feedback"
git push

# 12. Re-review after changes
/pr-review

# 13. Merge PR when approved (on GitHub/GitLab)
# - Use "Squash and merge" for clean history
# - Or "Merge commit" to preserve commit history

# 14. Delete feature branch
git checkout develop
git pull origin develop
git branch -d feature/add-category-sync
```

### Hotfix Workflow (Production Emergency)

```bash
# 1. Start hotfix from main
/hotfix-start critical-sync-error

# You'll be asked to confirm it's truly critical:
# - Production is broken
# - Needs immediate deployment
# - Cannot wait for next release

# 2. Fix ONLY the critical issue (minimal changes!)
# ... fix the bug ...

# 3. Test thoroughly
/run-tests all
/check-types

# 4. Review your changes
/review

# 5. Commit the fix
git add .
git commit -m "Fix critical sync error causing data loss"

# 6. Finish hotfix
/hotfix-finish

# This automatically:
# - Verifies you're on hotfix/* branch
# - Checks all changes committed
# - Rebases on latest main
# - Runs pr-reviewer with extra scrutiny
# - Provides instructions for TWO PRs (main and develop)

# 7. Create PR to main (production)
gh pr create --base main --head hotfix/critical-sync-error \
  --title "Hotfix: Critical sync error" \
  --body "Fixes data loss in sync operation"

# 8. Review hotfix (critical!)
/pr-review hotfix/critical-sync-error main

# 9. Merge to main when approved
# 10. Tag the release
git checkout main
git pull origin main
git tag -a v1.2.1 -m "Hotfix: Critical sync error"
git push origin v1.2.1

# 11. Deploy to production IMMEDIATELY

# 12. Create PR to develop (prevent regression)
gh pr create --base develop --head hotfix/critical-sync-error \
  --title "Merge hotfix: Critical sync error" \
  --body "Bringing hotfix back to develop"

# 13. Merge to develop
# 14. Delete hotfix branch
git branch -d hotfix/critical-sync-error
```

### Release Workflow

```bash
# 1. Start release from develop
/release-start v1.2.0

# This automatically:
# - Switches to develop
# - Pulls latest changes
# - Creates release/v1.2.0 branch
# - Provides release checklist

# 2. Update version numbers
# - frontend/package.json
# - backend/__init__.py or config
# - CHANGELOG.md

# Example: Update package.json
cd frontend
npm version 1.2.0 --no-git-tag-version
cd ..

# 3. Update CHANGELOG.md
# Add all features and fixes since last release

# 4. Final testing
/run-tests all
/check-types

# Test with real Magento instances
# Manual testing of critical features

# 5. Fix any last-minute bugs (NO NEW FEATURES!)
# ... fix bugs found in testing ...
git add .
git commit -m "Fix minor bug in comparison logic"

# 6. Finish release
/release-finish

# This automatically:
# - Runs comprehensive review
# - Checks version numbers updated
# - Verifies CHANGELOG.md complete
# - Ensures no new features (only bug fixes)
# - Provides instructions for merging to main and develop

# 7. Create PR to main (production)
gh pr create --base main --head release/v1.2.0 \
  --title "Release v1.2.0" \
  --body "Production release v1.2.0"

# 8. Review release
/pr-review release/v1.2.0 main

# 9. Merge to main when approved
# 10. Tag the release
git checkout main
git pull origin main
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0

# 11. Deploy to production

# 12. Create PR to develop (bring changes back)
gh pr create --base develop --head release/v1.2.0 \
  --title "Merge release v1.2.0 to develop" \
  --body "Bringing release changes back to develop"

# 13. Merge to develop
# 14. Delete release branch
git branch -d release/v1.2.0

# 15. Publish release notes
```

## 🔍 Code Review Process

### Mandatory Review Before Merge

**Every PR must be reviewed** using `/pr-review` before merging:

```bash
# Review any PR
/pr-review [source-branch] [target-branch]

# Examples:
/pr-review                                    # Current branch → develop
/pr-review feature/new-feature develop        # Specific branches
/pr-review hotfix/critical-fix main           # Hotfix to production
```

### What `/pr-review` Checks

The `pr-reviewer` subagent performs comprehensive checks:

#### 1. Git Flow Compliance ✅
- Branch naming follows conventions
- Source and target branches are correct
- No direct commits to main/develop
- Appropriate merge path

#### 2. Code Quality 🔍
- Frontend changes: Uses `frontend-reviewer`
- Backend changes: Uses `backend-reviewer`
- No code duplication
- Error handling present
- Follows project conventions

#### 3. Testing 🧪
- Tests included for new features
- All tests pass
- Type checking passes
- Coverage maintained or improved

#### 4. Security 🔐
- No hardcoded secrets
- Input validation present
- SQL injection prevention
- XSS vulnerabilities checked

#### 5. Merge Safety 🔀
- No merge conflicts
- Branch up-to-date with target
- Breaking changes documented
- Migration scripts included if needed

### Review Outcomes

The pr-reviewer provides one of three recommendations:

1. **✅ APPROVE** - Ready to merge
   - All checks pass
   - No critical issues
   - Tests pass
   - Git Flow compliant

2. **❌ REQUEST CHANGES** - Must fix before merge
   - Critical issues found
   - Tests failing
   - Security vulnerabilities
   - Git Flow violations

3. **💬 NEEDS DISCUSSION** - Requires team input
   - Architectural decisions
   - Breaking changes
   - Large refactorings
   - Unclear requirements

## 📊 Branching Best Practices

### Feature Branches

**Good Names:**
- `feature/add-widget-sync`
- `feature/TICKET-123-improve-diff-viewer`
- `feature/enhance-comparison-logic`

**Bad Names:**
- `my-feature` (use feature/ prefix)
- `test` (not descriptive)
- `feature/everything` (too broad)

**Tips:**
- Keep features focused and small
- One feature per branch
- Regularly rebase on develop
- Commit often with clear messages

### Hotfix Branches

**Good Names:**
- `hotfix/v1.2.1`
- `hotfix/critical-sync-data-loss`
- `hotfix/security-token-leak`

**Bad Names:**
- `hotfix/improvement` (not critical)
- `fix` (use hotfix/ prefix)

**Tips:**
- ONLY for production emergencies
- Minimal changes (fix only)
- Thorough testing required
- Deploy immediately after merge

### Release Branches

**Good Names:**
- `release/v1.2.0`
- `release/2.0.0`

**Bad Names:**
- `release/new-version` (use version number)
- `v1.2.0` (use release/ prefix)

**Tips:**
- Only bug fixes and version updates
- No new features
- Update CHANGELOG.md completely
- Test extensively before release

## 🛡️ Protected Branches

Configure GitHub/GitLab to protect `main` and `develop`:

```yaml
# GitHub: Settings → Branches → Branch protection rules

main:
  - Require pull request reviews before merging (1+ approvals)
  - Require status checks to pass (tests, type-check)
  - Require branches to be up to date
  - Do not allow bypassing the above settings
  - Restrict who can push to matching branches

develop:
  - Require pull request reviews before merging (1+ approvals)
  - Require status checks to pass (tests, type-check)
  - Require branches to be up to date
```

## 🎯 Team Roles

### Developer
- Creates feature/bugfix branches
- Makes changes and commits
- Runs `/feature-finish` when ready
- Creates PRs
- Addresses review feedback

### Code Reviewer
- Reviews PRs using `/pr-review`
- Checks Git Flow compliance
- Verifies code quality
- Approves or requests changes
- Merges approved PRs

### Release Manager
- Creates release branches with `/release-start`
- Updates version numbers
- Finalizes documentation
- Runs `/release-finish`
- Tags releases
- Coordinates deployments

### DevOps/SRE
- Handles hotfixes with `/hotfix-start`
- Deploys to production
- Monitors after deployment
- Merges hotfixes to develop

## 📚 Quick Reference

### Daily Commands

```bash
# Start your day
git checkout develop
git pull origin develop
/feature-start my-new-feature

# During development
/review                    # Review changes
/run-tests all            # Run tests
/check-types              # Check types
git commit -m "message"   # Commit

# End of feature
/feature-finish           # Review & create PR
/pr-review               # (Reviewer) Review PR
# Merge PR after approval
```

### Emergency Commands

```bash
# Production is broken!
/hotfix-start critical-issue
# ... fix issue ...
/run-tests all
/hotfix-finish
# Create PR, get review, merge, deploy
```

### Release Commands

```bash
# Release preparation
/release-start v1.2.0
# ... update versions, changelog ...
/run-tests all
/release-finish
# Create PR, get review, merge, tag, deploy
```

## 🆘 Troubleshooting

### "Not on a feature branch" Error
```bash
# You tried /feature-finish on wrong branch
git branch --show-current    # Check current branch
/feature-start <name>        # Start new feature
```

### Merge Conflicts
```bash
# During rebase
git status                   # See conflicted files
# ... resolve conflicts ...
git add <resolved-files>
git rebase --continue
/feature-finish             # Try again
```

### Failed PR Review
```bash
# pr-reviewer found issues
# Read the review output
# Fix critical issues
git add .
git commit -m "Fix review issues"
git push
/pr-review                  # Re-review
```

### Accidentally Committed to Develop
```bash
# Move commits to feature branch
git checkout develop
git log                     # Note commit hashes
git reset --hard origin/develop
git checkout -b feature/my-feature
git cherry-pick <commit-hash>
```

## 📖 Additional Resources

- [DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md) - Complete workflow guide
- [IMPROVEMENTS_SUMMARY.md](./IMPROVEMENTS_SUMMARY.md) - Overview of all improvements
- [CLAUDE.md](../CLAUDE.md) - AI development guide
- [.claude/QUICK_REFERENCE.md](../.claude/QUICK_REFERENCE.md) - Quick command reference

---

**Remember**: Git Flow is about safety, quality, and organization. Follow the process, use the tools, and your production deployments will be smooth and reliable! 🚀
