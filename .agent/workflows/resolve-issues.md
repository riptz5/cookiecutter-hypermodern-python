---
description: Automatically analyze and resolve GitHub issues using AI agent
---

1. Fetch open issues from GitHub
// turbo
python tools/resolve-issues.py --list

2. Analyze each issue to determine if it can be auto-resolved
// turbo
python tools/resolve-issues.py --analyze

3. Attempt to resolve issues automatically
// turbo
python tools/resolve-issues.py --resolve --dry-run

4. If dry-run successful, resolve for real
// turbo
python tools/resolve-issues.py --resolve

5. Create PRs for resolved issues
// turbo
python tools/resolve-issues.py --create-prs
