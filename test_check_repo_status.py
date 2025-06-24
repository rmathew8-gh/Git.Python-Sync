import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
import os
import subprocess
from check_repo_status import check_repo_status

@patch('check_repo_status.Repo')
def test_up_to_date(mock_repo):
    repo = MagicMock()
    branch = MagicMock()
    branch.name = 'main'
    repo.active_branch = branch
    repo.bare = False
    repo.remotes = {'origin': MagicMock()}
    repo.commit.side_effect = lambda x: x
    repo.iter_commits.side_effect = lambda x: iter([])
    repo.index.diff.return_value = []
    repo.untracked_files = []
    mock_repo.return_value = repo

    with patch('sys.stdout', new=StringIO()) as fake_out:
        check_repo_status()
        out = fake_out.getvalue()
        assert "up to date" in out
        assert "Working directory clean" in out

@patch('check_repo_status.Repo')
def test_ahead(mock_repo):
    repo = MagicMock()
    branch = MagicMock()
    branch.name = 'main'
    repo.active_branch = branch
    repo.bare = False
    repo.remotes = {'origin': MagicMock()}
    repo.commit.side_effect = lambda x: x
    repo.iter_commits.side_effect = lambda x: iter([1, 2]) if x == 'origin/main..main' else iter([])
    repo.index.diff.return_value = []
    repo.untracked_files = []
    mock_repo.return_value = repo

    with patch('sys.stdout', new=StringIO()) as fake_out:
        check_repo_status()
        out = fake_out.getvalue()
        assert "ahead of 'origin/main' by 2 commit(s)" in out
        assert "Working directory clean" in out

@patch('check_repo_status.Repo')
def test_behind(mock_repo):
    repo = MagicMock()
    branch = MagicMock()
    branch.name = 'main'
    repo.active_branch = branch
    repo.bare = False
    repo.remotes = {'origin': MagicMock()}
    repo.commit.side_effect = lambda x: x
    repo.iter_commits.side_effect = lambda x: iter([1, 2, 3]) if x == 'main..origin/main' else iter([])
    repo.index.diff.return_value = []
    repo.untracked_files = []
    mock_repo.return_value = repo

    with patch('sys.stdout', new=StringIO()) as fake_out:
        check_repo_status()
        out = fake_out.getvalue()
        assert "behind 'origin/main' by 3 commit(s)" in out
        assert "Working directory clean" in out

@patch('check_repo_status.Repo')
def test_diverged(mock_repo):
    repo = MagicMock()
    branch = MagicMock()
    branch.name = 'main'
    repo.active_branch = branch
    repo.bare = False
    repo.remotes = {'origin': MagicMock()}
    repo.commit.side_effect = lambda x: x
    repo.iter_commits.side_effect = lambda x: iter([1, 2]) if x == 'origin/main..main' else (iter([3]) if x == 'main..origin/main' else iter([]))
    repo.index.diff.return_value = []
    repo.untracked_files = []
    mock_repo.return_value = repo

    with patch('sys.stdout', new=StringIO()) as fake_out:
        check_repo_status()
        out = fake_out.getvalue()
        assert "diverged" in out
        assert "Working directory clean" in out

@patch('check_repo_status.Repo')
def test_staged_changes(mock_repo):
    repo = MagicMock()
    branch = MagicMock()
    branch.name = 'main'
    repo.active_branch = branch
    repo.bare = False
    repo.remotes = {'origin': MagicMock()}
    repo.commit.side_effect = lambda x: x
    repo.iter_commits.side_effect = lambda x: iter([])
    # Simulate staged changes
    repo.index.diff.side_effect = lambda x=None: [1] if x == "HEAD" else []
    repo.untracked_files = []
    mock_repo.return_value = repo

    with patch('sys.stdout', new=StringIO()) as fake_out:
        check_repo_status()
        out = fake_out.getvalue()
        assert "staged changes ready to be committed" in out

@patch('check_repo_status.Repo')
def test_unstaged_changes(mock_repo):
    repo = MagicMock()
    branch = MagicMock()
    branch.name = 'main'
    repo.active_branch = branch
    repo.bare = False
    repo.remotes = {'origin': MagicMock()}
    repo.commit.side_effect = lambda x: x
    repo.iter_commits.side_effect = lambda x: iter([])
    # Simulate unstaged changes
    repo.index.diff.side_effect = lambda x=None: [1] if x is None else []
    repo.untracked_files = []
    mock_repo.return_value = repo

    with patch('sys.stdout', new=StringIO()) as fake_out:
        check_repo_status()
        out = fake_out.getvalue()
        assert "unstaged changes in your working directory" in out

@patch('check_repo_status.Repo')
def test_untracked_files(mock_repo):
    repo = MagicMock()
    branch = MagicMock()
    branch.name = 'main'
    repo.active_branch = branch
    repo.bare = False
    repo.remotes = {'origin': MagicMock()}
    repo.commit.side_effect = lambda x: x
    repo.iter_commits.side_effect = lambda x: iter([])
    repo.index.diff.return_value = []
    repo.untracked_files = ['foo.txt', 'bar.py']
    mock_repo.return_value = repo

    with patch('sys.stdout', new=StringIO()) as fake_out:
        check_repo_status()
        out = fake_out.getvalue()
        assert "untracked files" in out
        assert "foo.txt" in out and "bar.py" in out

def test_invalid_path():
    result = subprocess.run([
        sys.executable, '-m', 'check_repo_status', '/not/a/real/path'
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert "does not exist" in result.stdout

def test_not_a_directory(tmp_path):
    file_path = tmp_path / "afile.txt"
    file_path.write_text("not a dir")
    result = subprocess.run([
        sys.executable, '-m', 'check_repo_status', str(file_path)
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert "is not a directory" in result.stdout

def test_not_a_git_repo(tmp_path):
    # tmp_path is a directory but not a git repo
    result = subprocess.run([
        sys.executable, '-m', 'check_repo_status', str(tmp_path)
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert "is not a git repository" in result.stdout

def make_fake_repo(ahead=0, behind=0, staged=0, unstaged=0, name='repo'):
    repo = MagicMock()
    branch = MagicMock()
    branch.name = 'main'
    repo.active_branch = branch
    repo.bare = False
    repo.remotes = {'origin': MagicMock()}
    repo.commit.side_effect = lambda x: x
    repo.iter_commits.side_effect = lambda x: iter([1]*ahead) if x == 'origin/main..main' else (iter([1]*behind) if x == 'main..origin/main' else iter([]))
    repo.index.diff.side_effect = lambda x=None: [1]*staged if x == "HEAD" else ([1]*unstaged if x is None else [])
    repo.untracked_files = []
    return repo

@patch('os.listdir')
@patch('os.path.isdir')
@patch('check_repo_status.multi_repo_status.Repo')
def test_multi_repo_status_table(mock_repo, mock_isdir, mock_listdir):
    from check_repo_status.multi_repo_status import report_multi_repo_status
    # Simulate three subdirs
    mock_listdir.return_value = ['repo1', 'repo2', 'repo3']
    mock_isdir.side_effect = lambda d: True
    # Setup fake repos for each
    def repo_side_effect(path):
        if path.endswith('repo1'):
            return make_fake_repo(ahead=2, behind=0, staged=1, unstaged=2, name='repo1')
        if path.endswith('repo2'):
            return make_fake_repo(ahead=0, behind=3, staged=0, unstaged=0, name='repo2')
        if path.endswith('repo3'):
            return make_fake_repo(ahead=1, behind=1, staged=0, unstaged=1, name='repo3')
        raise Exception('not a repo')
    mock_repo.side_effect = repo_side_effect
    # Patch print to capture output
    with patch('sys.stdout', new=StringIO()) as fake_out:
        report_multi_repo_status('parent')
        out = fake_out.getvalue()
        # Remove progress lines
        table_lines = '\n'.join(line for line in out.splitlines() if not line.strip().startswith('Checking repo'))
        # Check table header
        assert 'Repo' in table_lines and 'Ahead' in table_lines and 'Behind' in table_lines
        # Check terse values for each repo
        assert 'repo1' in table_lines and '2' in table_lines and '-' in table_lines
        assert 'repo2' in table_lines and '3' in table_lines
        assert 'repo3' in table_lines and '1' in table_lines
        # Check staged/unstaged only shown if ahead
        assert '1' in table_lines  # staged for repo1
        assert '2' in table_lines  # unstaged for repo1
        # repo2 should not show staged/unstaged since not ahead
        # repo3 should show unstaged since ahead
        assert table_lines.count('repo1') == 1
        assert table_lines.count('repo2') == 1
        assert table_lines.count('repo3') == 1 