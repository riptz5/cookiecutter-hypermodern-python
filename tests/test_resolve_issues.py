"""Tests for tools/resolve-issues.py"""
import subprocess
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from typing import Any

import pytest

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from resolve_issues import (
    get_github_repo,
    list_open_issues,
    can_auto_resolve,
    analyze_issue,
    git_command,
)


class TestGetGitHubRepo:
    """Tests for get_github_repo function."""
    
    @patch("resolve_issues.github3")
    def test_get_github_repo_success(self, mock_github3):
        """Test successful repository retrieval."""
        mock_github = Mock()
        mock_repo = Mock()
        mock_github.login.return_value = mock_github
        mock_github.repository.return_value = mock_repo
        mock_github3.login.return_value = mock_github
        
        result = get_github_repo("owner", "repo", "token")
        
        mock_github3.login.assert_called_once_with(token="token")
        mock_github.repository.assert_called_once_with("owner", "repo")
        assert result == mock_repo


class TestListOpenIssues:
    """Tests for list_open_issues function."""
    
    def test_list_open_issues_no_labels(self):
        """Test listing issues without label filter."""
        mock_repo = Mock()
        mock_issue1 = Mock()
        mock_issue2 = Mock()
        mock_repo.issues.return_value = [mock_issue1, mock_issue2]
        
        result = list_open_issues(mock_repo)
        
        mock_repo.issues.assert_called_once_with(state="open", labels=None)
        assert len(result) == 2
        assert result[0] == mock_issue1
        assert result[1] == mock_issue2
    
    def test_list_open_issues_with_labels(self):
        """Test listing issues with label filter."""
        mock_repo = Mock()
        mock_issue = Mock()
        mock_repo.issues.return_value = [mock_issue]
        
        result = list_open_issues(mock_repo, labels=["bug", "enhancement"])
        
        mock_repo.issues.assert_called_once_with(state="open", labels=["bug", "enhancement"])
        assert len(result) == 1


class TestCanAutoResolve:
    """Tests for can_auto_resolve function."""
    
    def test_cannot_resolve_assigned_issue(self):
        """Test that assigned issues cannot be auto-resolved."""
        mock_issue = Mock()
        mock_issue.assignee = Mock()  # Has assignee
        mock_issue.labels = []
        
        can_resolve, reason = can_auto_resolve(mock_issue)
        
        assert can_resolve is False
        assert "assigned" in reason.lower()
    
    def test_cannot_resolve_no_auto_resolve_label(self):
        """Test that issues with no-auto-resolve label cannot be resolved."""
        mock_issue = Mock()
        mock_issue.assignee = None
        mock_label = Mock()
        mock_label.name = "no-auto-resolve"
        mock_issue.labels = [mock_label]
        
        can_resolve, reason = can_auto_resolve(mock_issue)
        
        assert can_resolve is False
        assert "no-auto-resolve" in reason.lower()
    
    def test_cannot_resolve_question(self):
        """Test that question issues cannot be auto-resolved."""
        mock_issue = Mock()
        mock_issue.assignee = None
        mock_label = Mock()
        mock_label.name = "question"
        mock_issue.labels = [mock_label]
        
        can_resolve, reason = can_auto_resolve(mock_issue)
        
        assert can_resolve is False
        assert "question" in reason.lower()
    
    def test_can_resolve_simple_bug(self):
        """Test that simple bugs can be auto-resolved."""
        mock_issue = Mock()
        mock_issue.assignee = None
        mock_label1 = Mock()
        mock_label1.name = "bug"
        mock_label2 = Mock()
        mock_label2.name = "good first issue"
        mock_issue.labels = [mock_label1, mock_label2]
        
        can_resolve, reason = can_auto_resolve(mock_issue)
        
        assert can_resolve is True
        assert "bug" in reason.lower() or "simple" in reason.lower()
    
    def test_can_resolve_documentation(self):
        """Test that documentation issues can be auto-resolved."""
        mock_issue = Mock()
        mock_issue.assignee = None
        mock_label = Mock()
        mock_label.name = "documentation"
        mock_issue.labels = [mock_label]
        
        can_resolve, reason = can_auto_resolve(mock_issue)
        
        assert can_resolve is True
        assert "documentation" in reason.lower()
    
    def test_can_resolve_style(self):
        """Test that style issues can be auto-resolved."""
        mock_issue = Mock()
        mock_issue.assignee = None
        mock_label = Mock()
        mock_label.name = "style"
        mock_issue.labels = [mock_label]
        
        can_resolve, reason = can_auto_resolve(mock_issue)
        
        assert can_resolve is True
        assert "style" in reason.lower() or "formatting" in reason.lower()
    
    def test_can_resolve_dependencies(self):
        """Test that dependency issues can be auto-resolved."""
        mock_issue = Mock()
        mock_issue.assignee = None
        mock_label = Mock()
        mock_label.name = "dependencies"
        mock_issue.labels = [mock_label]
        
        can_resolve, reason = can_auto_resolve(mock_issue)
        
        assert can_resolve is True
        assert "dependency" in reason.lower()
    
    def test_can_resolve_template(self):
        """Test that template issues can be auto-resolved."""
        mock_issue = Mock()
        mock_issue.assignee = None
        mock_label = Mock()
        mock_label.name = "cookiecutter"
        mock_issue.labels = [mock_label]
        
        can_resolve, reason = can_auto_resolve(mock_issue)
        
        assert can_resolve is True
        assert "template" in reason.lower()


class TestAnalyzeIssue:
    """Tests for analyze_issue function."""
    
    def test_analyze_issue_basic(self, tmp_path):
        """Test basic issue analysis."""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "This is a test issue with `file.py` mentioned"
        mock_issue.labels = []
        
        result = analyze_issue(mock_issue, tmp_path)
        
        assert result["number"] == 123
        assert result["title"] == "Test Issue"
        assert "file.py" in result["mentioned_files"]
        assert "can_resolve" in result
        assert "reason" in result
    
    def test_analyze_issue_with_mentioned_files(self, tmp_path):
        """Test issue analysis with file mentions."""
        mock_issue = Mock()
        mock_issue.number = 456
        mock_issue.title = "Fix docs"
        mock_issue.body = "Fix `README.md` and `docs/index.md`"
        mock_issue.labels = []
        
        result = analyze_issue(mock_issue, tmp_path)
        
        assert "README.md" in result["mentioned_files"]
        assert "docs/index.md" in result["mentioned_files"]


class TestGitCommand:
    """Tests for git_command function."""
    
    @patch("resolve_issues.subprocess.run")
    def test_git_command_success(self, mock_run):
        """Test successful git command execution."""
        mock_result = Mock()
        mock_result.stdout = "success"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = git_command("status")
        
        mock_run.assert_called_once()
        assert result == mock_result
    
    @patch("resolve_issues.subprocess.run")
    def test_git_command_with_cwd(self, mock_run):
        """Test git command with custom working directory."""
        mock_result = Mock()
        mock_result.stdout = "success"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        test_path = Path("/test/path")
        
        git_command("status", cwd=test_path)
        
        call_args = mock_run.call_args
        assert call_args[1]["cwd"] == test_path
    
    @patch("resolve_issues.subprocess.run")
    @patch("resolve_issues.click.secho")
    def test_git_command_error(self, mock_secho, mock_run):
        """Test git command error handling."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", stderr="error message"
        )
        
        with pytest.raises(subprocess.CalledProcessError):
            git_command("invalid")
        
        mock_secho.assert_called_once()
        assert "error" in mock_secho.call_args[0][0].lower()
    
    @patch("resolve_issues.subprocess.run")
    def test_git_command_no_check(self, mock_run):
        """Test git command with check=False."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = git_command("status", check=False)
        
        assert result == mock_result
        # Should not raise exception


class TestIntegration:
    """Integration tests (mocked external dependencies)."""
    
    @patch("resolve_issues.github3")
    @patch("resolve_issues.subprocess.run")
    def test_full_workflow_mock(self, mock_subprocess, mock_github3):
        """Test full workflow with all mocks."""
        # Setup mocks
        mock_github = Mock()
        mock_repo = Mock()
        mock_issue = Mock()
        mock_issue.number = 1
        mock_issue.title = "Test"
        mock_issue.body = "Test body"
        mock_issue.assignee = None
        mock_issue.labels = []
        mock_issue.html_url = "https://github.com/owner/repo/issues/1"
        
        mock_repo.issues.return_value = [mock_issue]
        mock_github.login.return_value = mock_github
        mock_github.repository.return_value = mock_repo
        mock_github3.login.return_value = mock_github
        
        # Test workflow
        repo = get_github_repo("owner", "repo", "token")
        issues = list_open_issues(repo)
        can_resolve, reason = can_auto_resolve(issues[0])
        
        assert len(issues) == 1
        assert can_resolve is True  # Should be resolvable by default
