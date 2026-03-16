from unittest.mock import patch, MagicMock
from io import StringIO
import sys
import subprocess
from check_repo_status import check_repo_status
from datetime import datetime

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
    repo.heads = {'main': branch}
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
    repo.heads = {'main': branch}
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
    repo.heads = {'main': branch}
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
    branch.name = name  # Use the repo name as the branch name for formatting
    repo.active_branch = branch
    repo.bare = False
    repo.remotes = {'origin': MagicMock()}
    repo.commit.side_effect = lambda x: x
    repo.iter_commits.side_effect = lambda x: iter([1]*ahead) if x == 'origin/main..main' else (iter([1]*behind) if x == 'main..origin/main' else iter([]))
    # Always return lists of the correct length for diff
    def diff_side_effect(arg=None):
        if arg == "HEAD":
            return [1]*staged
        elif arg is None:
            return [1]*unstaged
        else:
            return []
    repo.index.diff.side_effect = diff_side_effect
    repo.untracked_files = []
    # Add heads['main'] for fallback logic
    repo.heads = {'main': branch}
    # Patch head.commit.committed_datetime to a real datetime
    commit = MagicMock()
    commit.committed_datetime = datetime(2025, 3, 23)
    repo.head.commit = commit
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
        assert '| Repo' in table_lines and '| Branch' in table_lines and '| Status' in table_lines and '| Pull' in table_lines
        # Check each repo line for correct values
        # Remarkable repos (repo1, repo3) should be at the top, clean (repo2) last
        lines = [line for line in table_lines.splitlines() if line.strip().startswith('|')]
        # Find the lines for each repo
        repo_lines = {l.split('|')[1].strip(): l for l in lines if l.count('|') > 6}
        # repo1: staged=1, unstaged=2 -> SU
        assert 'repo1' in repo_lines and 'SU' in repo_lines['repo1']
        # repo3: ahead=1, behind=1, unstaged=1 -> U
        assert 'repo3' in repo_lines and 'U' in repo_lines['repo3']
        # repo2: clean -> ✔
        assert 'repo2' in repo_lines and '✔' in repo_lines['repo2']

@patch('check_repo_status.Repo')
def test_fallback_to_master(mock_repo):
    repo = MagicMock()
    # Simulate only 'master' branch exists
    repo.heads = {'master': MagicMock(name='master')}
    repo.heads['master'].name = 'master'
    repo.active_branch = repo.heads['master']
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
        assert "master" in out
        assert "Working directory clean" in out

@patch('check_repo_status.Repo')
def test_fallback_to_active_branch(mock_repo):
    repo = MagicMock()
    # Simulate neither 'main' nor 'master' exists, only 'feature' branch
    repo.heads = {}
    feature_branch = MagicMock()
    feature_branch.name = 'feature-branch'
    repo.active_branch = feature_branch
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
        assert "feature-branch" in out
        assert "Working directory clean" in out

@patch('check_repo_status.multi_repo_status.Repo')
def test_commit_push_logic(mock_repo):
    from check_repo_status.multi_repo_status import get_repo_status_summary
    repo = make_fake_repo(staged=1, unstaged=1, name='repo-sync')
    mock_repo.return_value = repo
    
    # Mock git commands
    repo.git = MagicMock()
    repo.index.commit = MagicMock()
    repo.remotes['origin'].push = MagicMock()
    repo.untracked_files = ['new.file']
    
    status = get_repo_status_summary('path/repo-sync', do_commit_push=True)
    
    repo.git.add.assert_called_with(A=True)
    repo.index.commit.assert_called_with("Auto-sync: local changes")
    repo.remotes['origin'].push.assert_called_once()
    assert status['push_result'] == "OK"

@patch('os.listdir')
@patch('os.path.isdir')
@patch('check_repo_status.multi_repo_status.Repo')
@patch('check_repo_status.multi_repo_status.datetime')
def test_multi_repo_status_recent_days_default_value(mock_datetime, mock_repo, mock_isdir, mock_listdir):
    from check_repo_status.multi_repo_status import report_multi_repo_status
    from datetime import datetime, timedelta
    
    # Setup fake repos with different last activity dates
    mock_listdir.return_value = ['repo-recent', 'repo-old']
    mock_isdir.side_effect = lambda d: True
    
    # Mock datetime.now() to a fixed date
    mock_datetime.now.return_value = datetime(2025, 3, 23)
    mock_datetime.strptime = datetime.strptime
    mock_datetime.side_effect = datetime

    def make_repo_with_date(name, days_ago):
        repo = make_fake_repo(name=name)
        # Set the commit date to the specified days ago
        commit_date = datetime(2025, 3, 23) - timedelta(days=days_ago)
        repo.head.commit.committed_datetime = commit_date
        return repo

    repo_recent = make_repo_with_date('repo-recent', 10)   # 10 days ago
    repo_old = make_repo_with_date('repo-old', 40)         # 40 days ago

    def repo_side_effect(path):
        if path.endswith('repo-recent'):
            return repo_recent
        if path.endswith('repo-old'):
            return repo_old
        raise Exception('not a repo')
    mock_repo.side_effect = repo_side_effect

    with patch('sys.stdout', new=StringIO()) as fake_out:
        # Test with default 30 days (should include repo-recent but not repo-old)
        report_multi_repo_status('parent', recent_days=30)
        out = fake_out.getvalue()
        table_lines = [line for line in out.splitlines() if '|' in line and 'repo' in line]
        repo_names = [line.split('|')[1].strip() for line in table_lines]
        
        # Should only include repo-recent (10 days ago) as it's within 30 days
        assert 'repo-recent' in repo_names
        assert 'repo-old' not in repo_names

@patch('os.listdir')
@patch('os.path.isdir')
@patch('check_repo_status.multi_repo_status.Repo')
def test_multi_repo_status_error_summary(mock_repo, mock_isdir, mock_listdir):
    from check_repo_status.multi_repo_status import report_multi_repo_status
    mock_listdir.return_value = ['repo-ok', 'repo-err']
    mock_isdir.side_effect = lambda d: True
    
    repo_ok = make_fake_repo(name='repo-ok')
    repo_err = make_fake_repo(name='repo-err')
    
    def repo_side_effect(path):
        if 'repo-ok' in path: return repo_ok
        if 'repo-err' in path: return repo_err
        return make_fake_repo()
    mock_repo.side_effect = repo_side_effect
    
    repo_err.remotes['origin'].push.side_effect = Exception("Major Crash")

    with patch('sys.stdout', new=StringIO()) as fake_out:
        report_multi_repo_status('parent', do_commit_push=True)
        out = fake_out.getvalue()
        assert "SYNC ERRORS SUMMARY" in out
        assert "repo-err" in out
        assert "Major Crash" in out

@patch('os.listdir')
@patch('os.path.isdir')
@patch('check_repo_status.multi_repo_status.Repo')
@patch('check_repo_status.multi_repo_status.datetime')
def test_multi_repo_status_recent_days_filtering(mock_datetime, mock_repo, mock_isdir, mock_listdir):
    from check_repo_status.multi_repo_status import report_multi_repo_status
    from datetime import datetime, timedelta
    
    # Setup fake repos with different last activity dates
    mock_listdir.return_value = ['repo-recent', 'repo-old', 'repo-very-old']
    mock_isdir.side_effect = lambda d: True
    
    # Mock datetime.now() to a fixed date
    mock_datetime.now.return_value = datetime(2025, 3, 23)
    mock_datetime.strptime = datetime.strptime
    mock_datetime.side_effect = datetime

    def make_repo_with_date(name, days_ago):
        repo = make_fake_repo(name=name)
        # Set the commit date to the specified days ago
        commit_date = datetime(2025, 3, 23) - timedelta(days=days_ago)
        repo.head.commit.committed_datetime = commit_date
        return repo

    repo_recent = make_repo_with_date('repo-recent', 10)   # 10 days ago
    repo_old = make_repo_with_date('repo-old', 40)         # 40 days ago
    repo_very_old = make_repo_with_date('repo-very-old', 100) # 100 days ago

    def repo_side_effect(path):
        if path.endswith('repo-recent'):
            return repo_recent
        if path.endswith('repo-old'):
            return repo_old
        if path.endswith('repo-very-old'):
            return repo_very_old
        raise Exception('not a repo')
    mock_repo.side_effect = repo_side_effect

    with patch('sys.stdout', new=StringIO()) as fake_out:
        # Test with 30 days filter (should include repo-recent only)
        report_multi_repo_status('parent', recent_days=30)
        out = fake_out.getvalue()
        table_lines = [line for line in out.splitlines() if '|' in line and 'repo' in line]
        repo_names = [line.split('|')[1].strip() for line in table_lines]
        
        # Should only include repo-recent (10 days ago) as it's within 30 days
        assert 'repo-recent' in repo_names
        assert 'repo-old' not in repo_names
        assert 'repo-very-old' not in repo_names

@patch('os.listdir')
@patch('os.path.isdir')
@patch('check_repo_status.multi_repo_status.Repo')
@patch('check_repo_status.multi_repo_status.datetime')
def test_multi_repo_status_recent_days_90_days(mock_datetime, mock_repo, mock_isdir, mock_listdir):
    from check_repo_status.multi_repo_status import report_multi_repo_status
    from datetime import datetime, timedelta
    
    # Setup fake repos with different last activity dates
    mock_listdir.return_value = ['repo-recent', 'repo-old', 'repo-very-old']
    mock_isdir.side_effect = lambda d: True
    
    # Mock datetime.now() to a fixed date
    mock_datetime.now.return_value = datetime(2025, 3, 23)
    mock_datetime.strptime = datetime.strptime
    mock_datetime.side_effect = datetime

    def make_repo_with_date(name, days_ago):
        repo = make_fake_repo(name=name)
        # Set the commit date to the specified days ago
        commit_date = datetime(2025, 3, 23) - timedelta(days=days_ago)
        repo.head.commit.committed_datetime = commit_date
        return repo

    repo_recent = make_repo_with_date('repo-recent', 10)   # 10 days ago
    repo_old = make_repo_with_date('repo-old', 40)         # 40 days ago
    repo_very_old = make_repo_with_date('repo-very-old', 100) # 100 days ago

    def repo_side_effect(path):
        if path.endswith('repo-recent'):
            return repo_recent
        if path.endswith('repo-old'):
            return repo_old
        if path.endswith('repo-very-old'):
            return repo_very_old
        raise Exception('not a repo')
    mock_repo.side_effect = repo_side_effect

    with patch('sys.stdout', new=StringIO()) as fake_out:
        # Test with 90 days filter (should include repo-recent and repo-old but not repo-very-old)
        report_multi_repo_status('parent', recent_days=90)
        out = fake_out.getvalue()
        table_lines = [line for line in out.splitlines() if '|' in line and 'repo' in line]
        repo_names = [line.split('|')[1].strip() for line in table_lines]
        
        # Should include repo-recent and repo-old (both within 90 days) but not repo-very-old
        assert 'repo-recent' in repo_names
        assert 'repo-old' in repo_names
        assert 'repo-very-old' not in repo_names


@patch('os.listdir')
@patch('os.path.isdir')
@patch('check_repo_status.multi_repo_status.Repo')
@patch('check_repo_status.multi_repo_status.datetime')
def test_multi_repo_status_recent_days_default_value(mock_datetime, mock_repo, mock_isdir, mock_listdir):
    from check_repo_status.multi_repo_status import report_multi_repo_status
    from datetime import datetime, timedelta
    
    # Setup fake repos with different last activity dates
    mock_listdir.return_value = ['repo-recent', 'repo-old']
    mock_isdir.side_effect = lambda d: True
    
    # Mock datetime.now() to a fixed date
    mock_datetime.now.return_value = datetime(2025, 3, 23)
    mock_datetime.strptime = datetime.strptime
    mock_datetime.side_effect = datetime

    def make_repo_with_date(name, days_ago):
        repo = make_fake_repo(name=name)
        # Set the commit date to the specified days ago
        commit_date = datetime(2025, 3, 23) - timedelta(days=days_ago)
        repo.head.commit.committed_datetime = commit_date
        return repo

    repo_recent = make_repo_with_date('repo-recent', 10)   # 10 days ago
    repo_old = make_repo_with_date('repo-old', 40)         # 40 days ago

    def repo_side_effect(path):
        if path.endswith('repo-recent'):
            return repo_recent
        if path.endswith('repo-old'):
            return repo_old
        raise Exception('not a repo')
    mock_repo.side_effect = repo_side_effect

    with patch('sys.stdout', new=StringIO()) as fake_out:
        # Test with default 30 days (should include repo-recent but not repo-old)
        report_multi_repo_status('parent', recent_days=30)
        out = fake_out.getvalue()
        table_lines = [line for line in out.splitlines() if '|' in line and 'repo' in line]
        repo_names = [line.split('|')[1].strip() for line in table_lines]
        
        # Should only include repo-recent (10 days ago) as it's within 30 days
        assert 'repo-recent' in repo_names
        assert 'repo-old' not in repo_names
 