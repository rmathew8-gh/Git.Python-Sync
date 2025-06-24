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
    mock_repo.return_value = repo

    with patch('sys.stdout', new=StringIO()) as fake_out:
        check_repo_status()
        assert "up to date" in fake_out.getvalue()

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
    mock_repo.return_value = repo

    with patch('sys.stdout', new=StringIO()) as fake_out:
        check_repo_status()
        assert "ahead of 'origin/main' by 2 commit(s)" in fake_out.getvalue()

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
    mock_repo.return_value = repo

    with patch('sys.stdout', new=StringIO()) as fake_out:
        check_repo_status()
        assert "behind 'origin/main' by 3 commit(s)" in fake_out.getvalue()

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
    mock_repo.return_value = repo

    with patch('sys.stdout', new=StringIO()) as fake_out:
        check_repo_status()
        assert "diverged" in fake_out.getvalue()

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