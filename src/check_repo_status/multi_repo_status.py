import os
from git import Repo, GitCommandError, InvalidGitRepositoryError
from check_repo_status import should_fetch, update_fetch_cache
import sys
from datetime import datetime, timedelta


def get_repo_last_activity_local(repo_path):
    """Get just the local last commit date without fetching from remote.
    
    This is fast because it doesn't contact the remote server.
    Returns (repo_name, last_activity_datetime) or None if not a valid repo.
    """
    try:
        repo = Repo(repo_path)
    except (InvalidGitRepositoryError, GitCommandError, Exception):
        return None
    if repo.bare:
        return None
    try:
        last_commit_date = repo.head.commit.committed_datetime
        return (os.path.basename(repo_path), last_commit_date)
    except Exception:
        return None


def get_repo_status_summary(repo_path, do_pull=False, do_force=False, do_commit_push=False):
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
    remote_name = "origin"
    remote_branch = f"{remote_name}/{branch.name}"
    # Use fetch cache
    cache_seconds = int(os.environ.get("GIT_FETCH_CACHE_SECONDS", "600"))
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
    ahead = sum(1 for _ in repo.iter_commits(f"{remote_branch}..{branch.name}"))
    behind = sum(1 for _ in repo.iter_commits(f"{branch.name}..{remote_branch}"))
    staged = len(repo.index.diff("HEAD"))
    unstaged = len(repo.index.diff(None))
    untracked = len(repo.untracked_files)

    # Get last commit date in YYYY/MM/DD format
    try:
        last_commit_date = repo.head.commit.committed_datetime
        last_activity_str = last_commit_date.strftime("%Y/%m/%d")
    except Exception:
        last_activity_str = "-"

    # Perform commit first if commit-push is enabled, to ensure pull can succeed
    sync_error = None
    if do_commit_push:
        try:
            if staged or unstaged or untracked:
                repo.git.add(A=True)
                repo.index.commit("Auto-sync: local changes")
        except Exception as e:
            sync_error = f"Commit error: {e}"

    # Perform pull if requested
    pull_result = None
    if do_pull and not sync_error:
        try:
            pull_result = repo.remotes[remote_name].pull(branch.name)
        except Exception as e:
            pull_result = f"Error: {e}"
            if do_commit_push:
                sync_error = f"Pull error: {e}"

    # Perform push if requested
    push_result = None
    if do_commit_push and not sync_error:
        try:
            # Now push (includes any previously ahead commits + the one we just made)
            repo.remotes[remote_name].push()
            push_result = "OK"
        except Exception as e:
            push_result = f"Error: {e}"
            sync_error = f"Push error: {e}"

    return {
        "name": os.path.basename(repo_path),
        "branch": branch.name,
        "ahead": ahead,
        "behind": behind,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "cached": cache_hit,
        "pull_result": pull_result,
        "push_result": push_result,
        "sync_error": sync_error,
        "last_activity": last_activity_str,
    }


def report_multi_repo_status(
    parent_dir, do_pull=False, do_force=False, recent_days=None, do_commit_push=False
):
    subdirs = [
        os.path.join(parent_dir, d)
        for d in os.listdir(parent_dir)
        if os.path.isdir(os.path.join(parent_dir, d))
    ]
    
    # If recent_days filter is specified, first check local activity without fetching
    # This is much faster because we don't contact remote servers
    if recent_days is not None:
        # Calculate cutoff date (use naive datetime to match both naive and aware datetimes)
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        filtered_subdirs = []
        total = len(subdirs)
        for idx, subdir in enumerate(subdirs, 1):
            sys.stdout.write(
                f"Scanning repo {idx}/{total}: {os.path.basename(subdir)}...\r"
            )
            sys.stdout.flush()
            local_info = get_repo_last_activity_local(subdir)
            if local_info is not None:
                repo_name, last_activity = local_info
                # Handle timezone-aware vs naive datetime comparison
                # If last_activity has tzinfo but cutoff_date doesn't, strip tzinfo
                if last_activity.tzinfo is not None and cutoff_date.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=None)
                if last_activity >= cutoff_date:
                    filtered_subdirs.append(subdir)
        sys.stdout.write(" " * 80 + "\r")  # Clear the progress line
        sys.stdout.flush()
        subdirs_to_check = filtered_subdirs
        skipped_count = len(subdirs) - len(filtered_subdirs)
    else:
        subdirs_to_check = subdirs
        skipped_count = 0
    
    # Now only fetch and get full status for repos that passed the filter
    results = []
    total = len(subdirs_to_check)
    for idx, subdir in enumerate(subdirs_to_check, 1):
        sys.stdout.write(
            f"Checking repo {idx}/{total}: {os.path.basename(subdir)}...\r"
        )
        sys.stdout.flush()
        status = get_repo_status_summary(
            subdir,
            do_pull=do_pull,
            do_force=do_force,
            do_commit_push=do_commit_push,
        )
        if status:
            results.append(status)
    sys.stdout.write(" " * 80 + "\r")  # Clear the progress line
    sys.stdout.flush()

    # Helper to compute status symbol
    def compute_status(staged, unstaged, untracked):
        if staged and unstaged:
            status = "SU"
        elif staged:
            status = "S"
        elif unstaged:
            status = "U"
        elif untracked:
            status = "?"
        else:
            status = "✔"
        if untracked and (staged or unstaged):
            status += "?"
        return status

    def is_remarkable(r):
        return (
            compute_status(r["staged"], r["unstaged"], r["untracked"]) != "✔"
            or r.get("sync_error") is not None
        )

    def parse_last_activity(r):
        try:
            return datetime.strptime(r.get("last_activity", ""), "%Y/%m/%d")
        except Exception:
            return datetime.min

    # Filter by recent days if specified
    if recent_days is not None:
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        results = [r for r in results if parse_last_activity(r) >= cutoff_date]
    # Sort: remarkable first, then by last_activity desc, then by name
    results.sort(
        key=lambda r: (
            not is_remarkable(r),
            -parse_last_activity(r).timestamp(),
            r["name"],
        )
    )
    # Print org-mode table
    header = "| Repo                 | Ahead | Behind | Status | Last Activity | Pull                | Push      | Branch               | Cached  |"
    sep = "|----------------------+-------+--------+--------+---------------+---------------------+-----------+---------------------+---------|"
    print(header)
    print(sep)
    for r in results:
        ahead = str(r["ahead"]) if r["ahead"] else "-"
        behind = str(r["behind"]) if r["behind"] else "-"
        cached = "cached" if r.get("cached") else ""
        branch = str(r.get("branch", "-"))[:20]  # Truncate to 20 chars, fixed width
        repo_name = r["name"][:20]  # Truncate to 20 chars
        status = compute_status(r["staged"], r["unstaged"], r["untracked"])
        last_activity_col = r.get("last_activity", "-")
        # Format pull result for user-friendly output
        pull_result = r.get("pull_result")
        pull_col = ""
        if pull_result is not None:
            if isinstance(pull_result, list) and pull_result:
                changes = []
                for info in pull_result:
                    if hasattr(info, "ref") and hasattr(info, "note"):
                        changes.append(
                            f"{getattr(info, 'ref', '?')}: {getattr(info, 'note', '')}"
                        )
                if changes:
                    pull_col = ", ".join(changes)
                else:
                    pull_col = "OK"
            else:
                pull_col = str(pull_result)
        
        # Format push result / sync error
        push_result = r.get("push_result")
        sync_error = r.get("sync_error")
        push_col = ""
        if sync_error:
            push_col = f"ERR: {sync_error[:20]}"
        elif push_result is not None:
            push_col = str(push_result)

        print(
            f"| {repo_name:<20} | {ahead:<5} | {behind:<6} | {status:<6} | {last_activity_col:<13} | {pull_col:<19} | {push_col:<9} | {branch:<20} | {cached:<7} |"
        )
    # Print legend for Status column
    print("\nLegend for Status column:")
    print("  ✔  = Clean (no changes)")
    print("  S  = Staged changes only")
    print("  U  = Unstaged changes only")
    print("  ?  = Untracked files only")

    # Print summary showing checked vs displayed repos
    total_scanned = len(subdirs)
    displayed = len(results)

    print("\n" + "=" * 80)
    if recent_days is not None:
        print(f"SUMMARY: Scanned {total_scanned} repos, skipped {skipped_count} (older than {recent_days} days), showing {displayed} repos")
    else:
        print(f"SUMMARY: Checked {total_scanned} repos, showing {displayed} repos")
    print("=" * 80)

    # Print Error Summary Table if any errors occurred
    errors = [r for r in results if r.get("sync_error")]
    if errors:
        print("\n" + "=" * 80)
        print("SYNC ERRORS SUMMARY")
        print("=" * 80)
        err_header = f"| {'Repo':<25} | {'Error Message':<50} |"
        err_sep = f"|{'-' * 27}+{'-' * 52}|"
        print(err_header)
        print(err_sep)
        for e in errors:
            repo_name = e["name"][:25]
            err_msg = str(e["sync_error"])[:50]
            print(f"| {repo_name:<25} | {err_msg:<50} |")
        print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Check all subfolders for git repo status."
    )
    parser.add_argument("parent_dir", help="Directory containing subfolders to check.")
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Pull the current branch from the remote after checking status.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force fetch from remote, ignoring cache.",
    )
    parser.add_argument(
        "--recent-days",
        type=int,
        nargs='?',
        const=30,
        help="Only show repos with activity in the last N days (default: 30 when flag is used without value).",
    )
    parser.add_argument(
        "--commit-push",
        action="store_true",
        help="Commit and push local changes. Continues on failure and summarizes errors at the end.",
    )
    args = parser.parse_args()
    report_multi_repo_status(
        args.parent_dir,
        do_pull=args.pull,
        do_force=args.no_cache,
        recent_days=args.recent_days,
        do_commit_push=args.commit_push,
    )
