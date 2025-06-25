import os
from git import Repo, GitCommandError, InvalidGitRepositoryError
from check_repo_status import check_repo_status, should_fetch, update_fetch_cache
import sys
import time
from datetime import datetime, timedelta

def get_repo_status_summary(repo_path, do_pull=False, do_force=False):
    try:
        repo = Repo(repo_path)
    except (InvalidGitRepositoryError, GitCommandError, Exception):
        return None
    if repo.bare:
        return None
    # Always use the current active branch
    try:
        branch = repo.active_branch
    except Exception:
        # Fallback: try 'main' or 'master' if active branch is unavailable (detached HEAD)
        branch = None
        for branch_name in ["main", "master"]:
            try:
                branch_ref = repo.heads[branch_name]
                branch = branch_ref
                break
            except (IndexError, AttributeError, KeyError):
                continue
        if branch is None:
            return None
    remote_name = 'origin'
    remote_branch = f'{remote_name}/{branch.name}'
    # Use fetch cache
    cache_seconds = int(os.environ.get('GIT_FETCH_CACHE_SECONDS', '600'))
    fetch_needed = do_force or should_fetch(repo_path, remote_name, cache_seconds)
    cache_hit = False
    if fetch_needed:
        try:
            repo.remotes[remote_name].fetch()
            update_fetch_cache(repo_path, remote_name)
        except Exception:
            return None
    else:
        cache_hit = True
    # Try remote branch for current branch, then fallback to origin/main or origin/master
    remote_commit = None
    remote_branch_candidates = [remote_branch]
    # Fallbacks for legacy support
    if branch.name != "main":
        remote_branch_candidates.append(f"{remote_name}/main")
    if branch.name != "master":
        remote_branch_candidates.append(f"{remote_name}/master")
    for rb in remote_branch_candidates:
        try:
            remote_commit = repo.commit(rb)
            remote_branch = rb
            break
        except Exception:
            continue
    if remote_commit is None:
        return None
    ahead = sum(1 for _ in repo.iter_commits(f'{remote_branch}..{branch.name}'))
    behind = sum(1 for _ in repo.iter_commits(f'{branch.name}..{remote_branch}'))
    staged = len(repo.index.diff("HEAD"))
    unstaged = len(repo.index.diff(None))
    untracked = len(repo.untracked_files)

    # Get last commit date in YYYY/MM/DD format
    try:
        last_commit_date = repo.head.commit.committed_datetime
        last_activity_str = last_commit_date.strftime('%Y/%m/%d')
    except Exception:
        last_activity_str = '-'

    # Perform pull if requested
    pull_result = None
    if do_pull:
        try:
            pull_result = repo.remotes[remote_name].pull(branch.name)
        except Exception as e:
            pull_result = f"Error: {e}"

    return {
        'name': os.path.basename(repo_path),
        'branch': branch.name,
        'ahead': ahead,
        'behind': behind,
        'staged': staged,
        'unstaged': unstaged,
        'untracked': untracked,
        'cached': cache_hit,
        'pull_result': pull_result,
        'last_activity': last_activity_str,
    }

def report_multi_repo_status(parent_dir, do_pull=False, do_force=False):
    subdirs = [os.path.join(parent_dir, d) for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
    results = []
    total = len(subdirs)
    for idx, subdir in enumerate(subdirs, 1):
        sys.stdout.write(f"Checking repo {idx}/{total}: {os.path.basename(subdir)}...\r")
        sys.stdout.flush()
        status = get_repo_status_summary(subdir, do_pull=do_pull, do_force=do_force)
        if status:
            results.append(status)
    sys.stdout.write(' ' * 80 + '\r')  # Clear the progress line
    sys.stdout.flush()
    # Helper to compute status symbol
    def compute_status(staged, unstaged, untracked):
        if staged and unstaged:
            status = 'SU'
        elif staged:
            status = 'S'
        elif unstaged:
            status = 'U'
        elif untracked:
            status = '?'
        else:
            status = '✔'
        if untracked and (staged or unstaged):
            status += '?'
        return status
    # Sort results: remarkable (status != '✔') first (alphabetically), then clean (status == '✔') (alphabetically)
    def is_remarkable(r):
        return compute_status(r['staged'], r['unstaged'], r['untracked']) != '✔'
    def parse_last_activity(r):
        try:
            return datetime.strptime(r.get('last_activity', ''), '%Y/%m/%d')
        except Exception:
            return datetime.min
    # Sort: remarkable first, then by last_activity desc, then by name
    results.sort(key=lambda r: (not is_remarkable(r), -parse_last_activity(r).timestamp(), r['name']))
    # Print org-mode table
    header = '| Repo                 | Ahead | Behind | Status | Last Activity | Pull                | Branch               | Cached  |'
    sep    = '|----------------------+-------+--------+--------+---------------+---------------------+---------------------+---------|'
    print(header)
    print(sep)
    for r in results:
        ahead = str(r['ahead']) if r['ahead'] else "-"
        behind = str(r['behind']) if r['behind'] else "-"
        cached = 'cached' if r.get('cached') else ''
        branch = str(r.get('branch', '-'))[:20]  # Truncate to 20 chars, fixed width
        repo_name = r['name'][:20]  # Truncate to 20 chars
        status = compute_status(r['staged'], r['unstaged'], r['untracked'])
        last_activity_col = r.get('last_activity', '-')
        # Format pull result for user-friendly output
        pull_result = r.get('pull_result')
        pull_col = ''
        if pull_result is not None:
            if isinstance(pull_result, list) and pull_result:
                changes = []
                for info in pull_result:
                    if hasattr(info, 'ref') and hasattr(info, 'note'):
                        changes.append(f"{getattr(info, 'ref', '?')}: {getattr(info, 'note', '')}")
                if changes:
                    pull_col = ', '.join(changes)
                else:
                    pull_col = 'OK'
            else:
                pull_col = 'OK'
        print(f"| {repo_name:<20} | {ahead:<5} | {behind:<6} | {status:<6} | {last_activity_col:<13} | {pull_col:<19} | {branch:<20} | {cached:<7} |")
    # Print legend for Status column
    print("\nLegend for Status column:")
    print("  ✔  = Clean (no changes)")
    print("  S  = Staged changes only")
    print("  U  = Unstaged changes only")
    print("  ?  = Untracked files only")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Check all subfolders for git repo status.")
    parser.add_argument("parent_dir", help="Directory containing subfolders to check.")
    parser.add_argument("--pull", action="store_true", help="Pull the current branch from the remote after checking status.")
    parser.add_argument("--no-cache", action="store_true", help="Force fetch from remote, ignoring cache.")
    args = parser.parse_args()
    report_multi_repo_status(args.parent_dir, do_pull=args.pull, do_force=args.no_cache) 