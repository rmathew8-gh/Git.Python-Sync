import os
from git import Repo, GitCommandError, InvalidGitRepositoryError
from check_repo_status import check_repo_status, should_fetch, update_fetch_cache
import sys
import time

def get_repo_status_summary(repo_path):
    try:
        repo = Repo(repo_path)
    except (InvalidGitRepositoryError, GitCommandError, Exception):
        return None
    if repo.bare:
        return None
    try:
        branch = repo.active_branch
    except Exception:
        return None
    remote_name = 'origin'
    remote_branch = f'{remote_name}/{branch.name}'
    # Use fetch cache
    cache_seconds = int(os.environ.get('GIT_FETCH_CACHE_SECONDS', '600'))
    cache_hit = False
    if should_fetch(repo_path, remote_name, cache_seconds):
        try:
            repo.remotes[remote_name].fetch()
            update_fetch_cache(repo_path, remote_name)
        except Exception:
            return None
    else:
        cache_hit = True
    try:
        repo.commit(remote_branch)
    except Exception:
        return None
    ahead = sum(1 for _ in repo.iter_commits(f'{remote_branch}..{branch.name}'))
    behind = sum(1 for _ in repo.iter_commits(f'{branch.name}..{remote_branch}'))
    staged = len(repo.index.diff("HEAD"))
    unstaged = len(repo.index.diff(None))
    return {
        'name': os.path.basename(repo_path),
        'ahead': ahead,
        'behind': behind,
        'staged': staged,
        'unstaged': unstaged,
        'cached': cache_hit,
    }

def report_multi_repo_status(parent_dir):
    subdirs = [os.path.join(parent_dir, d) for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
    results = []
    total = len(subdirs)
    for idx, subdir in enumerate(subdirs, 1):
        sys.stdout.write(f"Checking repo {idx}/{total}: {os.path.basename(subdir)}...\r")
        sys.stdout.flush()
        status = get_repo_status_summary(subdir)
        if status:
            results.append(status)
    sys.stdout.write(' ' * 80 + '\r')  # Clear the progress line
    sys.stdout.flush()
    # Print org-mode table
    header = '| Repo                | Cached  | Ahead | Behind | Staged | Unstaged |'
    sep    = '|---------------------+---------+-------+--------+--------+----------|'
    print(header)
    print(sep)
    for r in results:
        ahead = str(r['ahead']) if r['ahead'] else "-"
        behind = str(r['behind']) if r['behind'] else "-"
        staged = str(r['staged']) if r['ahead'] and r['staged'] else "-"
        unstaged = str(r['unstaged']) if r['ahead'] and r['unstaged'] else "-"
        cached = 'cached' if r.get('cached') else ''
        print(f"| {r['name']:<19} | {cached:<7} | {ahead:<5} | {behind:<6} | {staged:<6} | {unstaged:<8} |")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Check all subfolders for git repo status.")
    parser.add_argument("parent_dir", help="Directory containing subfolders to check.")
    args = parser.parse_args()
    report_multi_repo_status(args.parent_dir) 