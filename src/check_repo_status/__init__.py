import sys
from git import Repo, GitCommandError
import os
import json
import time


def should_fetch(repo_path, remote_name, cache_seconds=60):
    cache_file = os.path.join(repo_path, ".git", ".fetch_cache.json")
    now = time.time()
    try:
        with open(cache_file, "r") as f:
            cache = json.load(f)
        last_fetch = cache.get(remote_name, 0)
        if now - last_fetch < cache_seconds:
            return False
    except Exception:
        pass
    return True


def update_fetch_cache(repo_path, remote_name):
    cache_file = os.path.join(repo_path, ".git", ".fetch_cache.json")
    try:
        cache = {}
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                cache = json.load(f)
        cache[remote_name] = time.time()
        with open(cache_file, "w") as f:
            json.dump(cache, f)
    except Exception:
        pass


def check_repo_status(repo_path=".", do_pull=False, do_force=False):
    try:
        repo = Repo(repo_path)
    except Exception as e:
        print(
            f"Error: Could not open the repository at '{repo_path}'. Please check that the directory exists and is a valid git repository.\nDetails: {e}"
        )
        sys.exit(1)

    if repo.bare:
        print("Repository is bare.")
        sys.exit(1)

    # Determine branch: prefer 'main', fallback to 'master'
    branch = None
    for branch_name in ["main", "master"]:
        try:
            branch_ref = repo.heads[branch_name]
            branch = branch_ref
            break
        except (IndexError, AttributeError, KeyError):
            continue
    if branch is None:
        # fallback to active_branch (for feature branches, etc.)
        try:
            branch = repo.active_branch
        except TypeError:
            print("Detached HEAD state. Please checkout a branch.")
            sys.exit(1)

    remote_name = "origin"
    remote_branch = f"{remote_name}/{branch.name}"

    # Fetch latest from remote, with caching
    cache_seconds = int(os.environ.get("GIT_FETCH_CACHE_SECONDS", "600"))
    fetch_needed = do_force or should_fetch(repo_path, remote_name, cache_seconds)
    if fetch_needed:
        try:
            repo.remotes[remote_name].fetch()
            update_fetch_cache(repo_path, remote_name)
        except IndexError:
            available_remotes = [r.name for r in repo.remotes]
            if available_remotes:
                print(
                    f"Error: Remote '{remote_name}' not found. Available remotes: {available_remotes}"
                )
            else:
                print(
                    f"Error: No git remotes found in this repository. Please add a remote named '{remote_name}' or specify an existing one."
                )
            sys.exit(1)
        except GitCommandError as e:
            print(f"Failed to fetch from remote: {e}")
            sys.exit(1)

    # Get commit objects
    try:
        repo.commit(branch.name)
    except Exception:
        print(f"Local branch {branch.name} not found.")
        sys.exit(1)
    # Try remote branch for current branch, then fallback to origin/main or origin/master
    remote_commit = None
    remote_branch_candidates = [remote_branch]
    # If current branch is main, try master as fallback; if master, try main as fallback
    if branch.name == "main":
        remote_branch_candidates.append(f"{remote_name}/master")
    elif branch.name == "master":
        remote_branch_candidates.append(f"{remote_name}/main")
    for rb in remote_branch_candidates:
        try:
            remote_commit = repo.commit(rb)
            remote_branch = rb  # Use the found remote branch for all further output
            break
        except Exception:
            continue
    if remote_commit is None:
        print(f"Remote branch {remote_branch} not found.")
        sys.exit(1)

    # Calculate ahead/behind
    ahead = sum(1 for _ in repo.iter_commits(f"{remote_branch}..{branch.name}"))
    behind = sum(1 for _ in repo.iter_commits(f"{branch.name}..{remote_branch}"))

    if ahead == 0 and behind == 0:
        print(f"Your branch '{branch.name}' is up to date with '{remote_branch}'.")
    elif ahead > 0 and behind == 0:
        print(
            f"Your branch '{branch.name}' is ahead of '{remote_branch}' by {ahead} commit(s). You may want to push."
        )
    elif ahead == 0 and behind > 0:
        print(
            f"Your branch '{branch.name}' is behind '{remote_branch}' by {behind} commit(s). You may want to pull."
        )
    else:
        print(
            f"Your branch and '{remote_branch}' have diverged. Local is ahead by {ahead} and behind by {behind} commit(s). Consider merging or rebasing."
        )

    # Check for staged, unstaged, and untracked changes
    staged_changes = repo.index.diff("HEAD")
    unstaged_changes = repo.index.diff(None)
    untracked_files = repo.untracked_files

    if staged_changes:
        print("There are staged changes ready to be committed.")
    if unstaged_changes:
        print("There are unstaged changes in your working directory.")
    if untracked_files:
        print(f"There are untracked files: {', '.join(untracked_files)}")
    if not staged_changes and not unstaged_changes and not untracked_files:
        print("Working directory clean (no staged, unstaged, or untracked changes).")

    # Perform pull if requested
    if do_pull:
        try:
            print(f"Pulling from {remote_name}/{branch.name}...")
            pull_info = repo.remotes[remote_name].pull(branch.name)
            print(f"Pull result: {pull_info}")
        except Exception as e:
            print(f"Error during pull: {e}")
