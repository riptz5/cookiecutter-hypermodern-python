# Creating GitHub Issues from Development Plan

This directory contains tools to create GitHub issues from the development plan.

## Files

- **`DEVELOPMENT_PLAN.md`**: Comprehensive roadmap with all milestones (M1-M4)
- **`create_issues.sh`**: Script to automatically create all issues in GitHub
- **`ISSUES_README.md`**: This file

## Quick Start

### Prerequisites

1. Install GitHub CLI:
   ```bash
   brew install gh
   ```

2. Authenticate with GitHub:
   ```bash
   gh auth login
   ```

### Create All Issues

Simply run the script:

```bash
./create_issues.sh
```

This will create **21 issues** across 4 milestones:

| Milestone | Issues | Focus |
|-----------|--------|-------|
| M1 | 4 | Google ADK Integration |
| M2 | 5 | MCP (Model Context Protocol) Integration |
| M3 | 4 | Agent Bridge & Adapters |
| M4 | 8 | Advanced Features & Polish |

### View Issues

After creation, view them at:
https://github.com/riptz5/cookiecutter-hypermodern-python/issues

## Issue Labels

The script automatically applies these labels:

- `enhancement` - New features
- `testing` - Test-related issues
- `documentation` - Documentation updates
- `security` - Security improvements
- `milestone:m1`, `milestone:m2`, `milestone:m3`, `milestone:m4` - Milestone tracking

## Manual Issue Creation

If you prefer to create issues manually, use `DEVELOPMENT_PLAN.md` as reference. Each issue includes:

- **Goal**: What the issue aims to achieve
- **Tasks**: Checklist of specific tasks
- **Acceptance Criteria**: Definition of done
- **Milestone**: Which milestone it belongs to

## Development Workflow

For each issue:

1. **Create branch**: `git checkout -b feature/issue-XX-description`
2. **Implement**: Follow TDD approach (test first)
3. **Test**: Ensure 100% coverage, all tests pass
4. **Validate**: Run template generation and validation
5. **Document**: Update relevant documentation
6. **PR**: Create pull request with clear description
7. **Review**: Address feedback, merge when approved

## Current Status

- ✅ **M0 (Foundation)**: Completed
- 🔨 **M1 (Google ADK)**: In Progress (branch: feature/m2-google-adk)
- 📋 **M2 (MCP)**: Planned
- 📋 **M3 (Bridge & Adapters)**: Planned
- 📋 **M4 (Advanced Features)**: Planned

## Notes

- All issues follow Hypermodern Python principles: simplicity, automation, reliability
- Agent features are opt-in via cookiecutter variables
- 100% test coverage is required for all code
- Generated projects without agent features remain identical to vanilla template

## Support

For questions or issues with the development plan:
1. Check `DEVELOPMENT_PLAN.md` for detailed information
2. Review existing issues for similar topics
3. Open a discussion on GitHub

---

**Last Updated**: December 26, 2025
