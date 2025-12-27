# Issue Resolution Procedure - Standard Operating Procedure

> **Purpose**: Automatically resolve GitHub issues using AI agent capabilities.
> **Audience**: AI agents and developers working on this cookiecutter template.

## 🎯 Core Principle

**Primary Directive**: Automatically analyze and resolve GitHub issues that can be safely handled by an AI agent, reducing manual work and improving response time.

## 📋 Standard Issue Resolution Workflow

### 1. Prerequisites

```bash
# Ensure GitHub CLI is authenticated
gh auth status

# Set environment variables (or use --token flag)
export GITHUB_USER="your-username"
export GITHUB_REPOSITORY="cookiecutter-hypermodern-python"
export GITHUB_TOKEN="your-token"
```

### 2. List Open Issues

```bash
# List all open issues
python tools/resolve-issues.py --list

# List issues with specific labels
python tools/resolve-issues.py --list --label bug --label "good first issue"
```

### 3. Analyze Issues

```bash
# Analyze which issues can be auto-resolved
python tools/resolve-issues.py --analyze

# Analyze specific labels
python tools/resolve-issues.py --analyze --label documentation
```

**Analysis Criteria:**
- ✅ **Can resolve**: Simple bugs, docs, style fixes, dependencies, template improvements
- ❌ **Cannot resolve**: Assigned issues, questions, discussions, complex features

### 4. Resolve Issues (Dry Run First)

```bash
# Dry run - see what would be done without making changes
python tools/resolve-issues.py --resolve --dry-run

# Resolve for real (after verifying dry-run)
python tools/resolve-issues.py --resolve --no-dry-run

# Limit number of issues processed
python tools/resolve-issues.py --resolve --limit 5
```

### 5. Create Pull Requests

```bash
# Create PRs for resolved issues
python tools/resolve-issues.py --create-prs
```

## 🔍 Issue Resolution Logic

### Issues That CAN Be Auto-Resolved

1. **Documentation Updates**
   - Fix typos
   - Update examples
   - Improve clarity
   - Add missing docs

2. **Code Style/Formatting**
   - Black formatting
   - isort imports
   - PEP 8 fixes
   - Type hints

3. **Simple Bug Fixes**
   - Syntax errors
   - Import errors
   - Obvious logic errors
   - Missing error handling

4. **Dependency Updates**
   - Security updates
   - Version bumps
   - Dependency additions

5. **Template Improvements**
   - Jinja2 fixes
   - Template structure
   - Configuration updates

### Issues That CANNOT Be Auto-Resolved

1. **Assigned Issues** - Human is working on it
2. **Questions/Discussions** - Need human input
3. **Complex Features** - Require design decisions
4. **Breaking Changes** - Need approval
5. **Issues with "no-auto-resolve" label** - Explicitly excluded

## 🚀 Quick Reference

### Full Workflow

```bash
# 1. List issues
python tools/resolve-issues.py --list

# 2. Analyze
python tools/resolve-issues.py --analyze

# 3. Dry run
python tools/resolve-issues.py --resolve --dry-run

# 4. Resolve (if dry-run looks good)
python tools/resolve-issues.py --resolve --no-dry-run

# 5. Create PRs
python tools/resolve-issues.py --create-prs
```

### Using Nox

```bash
# Run issue resolution workflow
nox -s resolve-issues

# Dry run only
nox -s resolve-issues -- --dry-run

# Analyze only
nox -s resolve-issues -- --analyze
```

## ⚠️ Safety Measures

### Dry Run by Default
- Always run with `--dry-run` first
- Review what would be changed
- Only use `--no-dry-run` after verification

### Issue Filtering
- Only process issues that match criteria
- Skip assigned issues
- Respect "no-auto-resolve" label

### Testing Before PR
- All changes must pass tests
- Template must generate successfully
- No Jinja artifacts left behind

### PR Requirements
- Clear description of changes
- Link to original issue
- Tests included (if applicable)
- Follow project conventions

## 📝 Resolution Process

For each resolvable issue:

1. **Analyze Issue**
   - Read title and description
   - Identify files mentioned
   - Determine type of fix needed

2. **Create Branch**
   - Branch name: `auto-resolve-{issue-number}`
   - Base: `main`

3. **Make Changes**
   - Implement fix
   - Follow coding standards
   - Update tests if needed

4. **Validate**
   - Run tests: `nox -s tests`
   - Validate template: `cookiecutter . --no-input`
   - Check coverage: 100%

5. **Create PR**
   - Title: `[Auto] Fix #{issue_number}: {title}`
   - Body: Description + link to issue
   - Labels: Appropriate labels

6. **Comment on Issue**
   - Link to PR
   - Explain what was done

## 🎯 Success Criteria

Before considering an issue resolved:

- ✅ Issue analysis completed
- ✅ Changes implemented
- ✅ Tests pass (100% coverage)
- ✅ Template validates
- ✅ PR created and linked
- ✅ Issue commented with PR link

## 🔄 Continuous Improvement

This procedure should be updated when:
- New resolution patterns emerge
- Safety measures need adjustment
- Better practices are discovered
- New issue types are identified

**Location**: `.agent/procedures/ISSUE_RESOLUTION_PROCEDURE.md`
**Owner**: All agents and developers
**Review**: After every major resolution

---

**Remember**: Safety first. Always dry-run before making real changes.
