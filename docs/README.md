# Magento CMS Sync - Documentation Hub

**Welcome to the complete documentation for the Magento CMS Sync project.**

> 📍 **New to the project?** Start with the [Getting Started](#-getting-started) section below.

---

## 🗺️ Documentation Map

### 🚀 Start Here

| Document | Purpose | Audience |
|----------|---------|----------|
| **This Page** | Documentation hub and navigation | Everyone |
| [../README.md](../README.md) | Project overview, installation, usage | Users, New Developers |
| [IMPROVEMENTS_SUMMARY.md](./IMPROVEMENTS_SUMMARY.md) | What's new and changed | Team Leads, Developers |

### 👨‍💻 For Developers

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md) | **Daily reference** - Subagents, commands, workflows | Every day |
| [GIT_FLOW_GUIDE.md](./GIT_FLOW_GUIDE.md) | Complete Git Flow workflow guide | When working on features/releases |
| [../.claude/QUICK_REFERENCE.md](../.claude/QUICK_REFERENCE.md) | **Command cheat sheet** - Keep open | Every day |
| [MANUAL_TESTING_CHECKLIST.md](./MANUAL_TESTING_CHECKLIST.md) | QA and testing checklist | Before releases |
| [LOCAL_MAGENTO_INSTANCES.md](./LOCAL_MAGENTO_INSTANCES.md) | Two real Magento instances on one machine for end-to-end testing and screenshots | Manual QA, docs |

### 📊 For Team Leads

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [CODE_REVIEW_REPORT.md](./CODE_REVIEW_REPORT.md) | Code quality assessment & action plan | Sprint planning |
| [IMPROVEMENTS_SUMMARY.md](./IMPROVEMENTS_SUMMARY.md) | Overview of new features & impact | Team updates |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Production deployment guide | Releases |

### 🔧 For Operations

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Deployment instructions | Production releases |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | Common issues & solutions | When issues occur |

---

## 📚 Document Descriptions

### Core Documentation

#### [DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md)
> **For**: Developers (Daily Reference)
> **Size**: 16KB
> **Updated**: 2024-10-31

Your daily development reference covering:
- Git Flow workflow overview
- 6 specialized subagents (what they do, when to use)
- 16 slash commands (Git Flow, development, Magento)
- Complete workflow examples (feature, hotfix, release)
- Debugging workflows
- Testing workflows

**Use this when**: You need to know what command to run or how to use a subagent.

---

#### [GIT_FLOW_GUIDE.md](./GIT_FLOW_GUIDE.md)
> **For**: Developers (Workflow Reference)
> **Size**: 14KB
> **Updated**: 2024-10-31

Complete Git Flow integration guide:
- Branch structure and naming
- Feature, hotfix, and release workflows
- Step-by-step command examples
- Code review process (pr-reviewer)
- Protected branch configuration
- Team roles and responsibilities
- Troubleshooting Git Flow issues

**Use this when**: Starting a new feature, release, or hotfix.

---

#### [CODE_REVIEW_REPORT.md](./CODE_REVIEW_REPORT.md)
> **For**: Team Leads, Developers
> **Size**: 14KB
> **Updated**: 2024-10-31

Comprehensive code quality assessment:
- Overall quality scores (Backend: 7.5/10, Frontend: 8.5/10)
- 4 critical backend issues (must fix before production)
- 13 important issues (should fix soon)
- Best practices followed
- Action plan with time estimates
- Deployment recommendation

**Use this when**: Planning sprints or preparing for production deployment.

---

#### [IMPROVEMENTS_SUMMARY.md](./IMPROVEMENTS_SUMMARY.md)
> **For**: Everyone (Overview)
> **Size**: 12KB
> **Updated**: 2024-10-31

High-level summary of all improvements:
- What changed (before/after comparison)
- New features (Git Flow, subagents, commands)
- Time savings (7 hours/week per developer)
- Getting started guides
- Next steps and priorities
- Impact assessment

**Use this when**: You want a quick overview of what's new.

---

### Supporting Documentation

#### [DEPLOYMENT.md](./DEPLOYMENT.md)
> **For**: DevOps, Team Leads
> **Size**: 6KB

Production deployment instructions and configuration.

#### [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
> **For**: Developers, Support
> **Size**: 4KB

Common issues and their solutions.

#### [MANUAL_TESTING_CHECKLIST.md](./MANUAL_TESTING_CHECKLIST.md)
> **For**: QA, Developers
> **Size**: 12KB

Step-by-step manual testing procedures.

#### [../.claude/QUICK_REFERENCE.md](../.claude/QUICK_REFERENCE.md)
> **For**: Developers (Daily)
> **Size**: 3KB

One-page cheat sheet of all commands. **Keep this open while coding!**

---

## 🚀 Getting Started

### New Developer Onboarding

**Day 1**: Understand the Project
1. Read [../README.md](../README.md) - Project overview
2. Set up your development environment
3. Run `./start-dev.sh` to start the app

**Day 2**: Learn the Workflow
1. Read [DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md)
2. Try your first feature: `/feature-start onboarding-test`
3. Make a small change, commit, run `/feature-finish`
4. See the pr-reviewer in action with `/pr-review`

**Day 3**: Deep Dive
1. Read [GIT_FLOW_GUIDE.md](./GIT_FLOW_GUIDE.md)
2. Review [CODE_REVIEW_REPORT.md](./CODE_REVIEW_REPORT.md)
3. Bookmark [../.claude/QUICK_REFERENCE.md](../.claude/QUICK_REFERENCE.md)

**Ongoing**: Keep [../.claude/QUICK_REFERENCE.md](../.claude/QUICK_REFERENCE.md) open!

---

### Quick Task Reference

| I want to... | Command/Document |
|--------------|------------------|
| **Start a new feature** | `/feature-start <name>` → [GIT_FLOW_GUIDE.md](./GIT_FLOW_GUIDE.md) |
| **Review my changes** | `/review` |
| **Run tests** | `/run-tests all` |
| **Check types** | `/check-types` |
| **Finish feature** | `/feature-finish` |
| **Review PR** | `/pr-review` ⚠️ Required before merge |
| **Debug Magento API** | `/debug-api <id>` |
| **Validate sync** | `/check-sync` |
| **Generate tests** | `/add-test <file>` |
| **Fix production bug** | `/hotfix-start <name>` → [GIT_FLOW_GUIDE.md](./GIT_FLOW_GUIDE.md#hotfix-workflow) |
| **Prepare release** | `/release-start <version>` → [GIT_FLOW_GUIDE.md](./GIT_FLOW_GUIDE.md#release-workflow) |

---

## 🎯 Common Scenarios

### Scenario: I'm Starting a New Feature

1. **Start feature branch**:
   ```bash
   /feature-start add-widget-sync
   ```

2. **Read relevant docs**:
   - Workflow: [DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md)
   - Git Flow: [GIT_FLOW_GUIDE.md](./GIT_FLOW_GUIDE.md)

3. **Develop** (use [../.claude/QUICK_REFERENCE.md](../.claude/QUICK_REFERENCE.md) for commands)

4. **Review**:
   ```bash
   /review
   /run-tests all
   /check-types
   ```

5. **Finish**:
   ```bash
   /feature-finish  # Triggers pr-reviewer
   ```

---

### Scenario: Production is Broken (Hotfix)

1. **Start hotfix**:
   ```bash
   /hotfix-start critical-sync-bug
   ```

2. **Fix the issue** (minimal changes only!)

3. **Test thoroughly**:
   ```bash
   /run-tests all
   /check-types
   /review
   ```

4. **Finish hotfix**:
   ```bash
   /hotfix-finish  # Creates 2 PRs: main + develop
   ```

5. **Follow instructions** to merge and deploy

📖 **Full guide**: [GIT_FLOW_GUIDE.md - Hotfix Workflow](./GIT_FLOW_GUIDE.md#hotfix-workflow-production-emergency)

---

### Scenario: Preparing a Release

1. **Start release**:
   ```bash
   /release-start v1.2.0
   ```

2. **Update versions** (package.json, backend, CHANGELOG.md)

3. **Final testing**:
   ```bash
   /run-tests all
   /check-types
   ```

4. **Finish release**:
   ```bash
   /release-finish
   ```

5. **Merge to main** → **Tag** → **Deploy**

📖 **Full guide**: [GIT_FLOW_GUIDE.md - Release Workflow](./GIT_FLOW_GUIDE.md#release-workflow)

---

## 🔍 Finding What You Need

### By Role

- **New Developer**: [Getting Started](#-getting-started)
- **Developer (Daily Work)**: [DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md) + [Quick Reference](../.claude/QUICK_REFERENCE.md)
- **Team Lead**: [CODE_REVIEW_REPORT.md](./CODE_REVIEW_REPORT.md)
- **DevOps**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **QA**: [MANUAL_TESTING_CHECKLIST.md](./MANUAL_TESTING_CHECKLIST.md)

> **Note for AI Assistants**: The primary AI prompt is `../CLAUDE.md` in the root directory (always loaded). This `docs/` folder contains human-focused reference documentation.

### By Topic

- **Git Flow**: [GIT_FLOW_GUIDE.md](./GIT_FLOW_GUIDE.md)
- **Subagents**: [DEVELOPMENT_WORKFLOW.md - Subagents](./DEVELOPMENT_WORKFLOW.md#subagents)
- **Slash Commands**: [../.claude/QUICK_REFERENCE.md](../.claude/QUICK_REFERENCE.md)
- **Code Quality**: [CODE_REVIEW_REPORT.md](./CODE_REVIEW_REPORT.md)
- **What's New**: [IMPROVEMENTS_SUMMARY.md](./IMPROVEMENTS_SUMMARY.md)

### By Task

Use the [Quick Task Reference](#quick-task-reference) table above.

---

## 📊 Documentation Statistics

| Metric | Count |
|--------|-------|
| **Total Documents** | 8 (in docs/) + 1 (CLAUDE.md in root) |
| **Total Size** | ~95KB |
| **Subagents** | 6 |
| **Slash Commands** | 15 |
| **Coverage** | 95% |

---

## 🆘 Need Help?

1. **Can't find what you need?** Check the [Document Index](#-document-descriptions) above
2. **Command not working?** See [../.claude/QUICK_REFERENCE.md](../.claude/QUICK_REFERENCE.md)
3. **Git Flow confused?** Read [GIT_FLOW_GUIDE.md](./GIT_FLOW_GUIDE.md)
4. **App not working?** Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
5. **Still stuck?** Ask the team or check project README

---

## 🔄 Keeping Documentation Updated

When updating docs:
1. Update the specific document
2. Update cross-references if needed
3. Update this index if structure changes
4. Update [IMPROVEMENTS_SUMMARY.md](./IMPROVEMENTS_SUMMARY.md) if major changes
5. Update "Last Updated" dates

---

**Last Updated**: 2024-10-31
**Maintained By**: Development Team
**Version**: 2.0
