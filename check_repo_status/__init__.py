import sys
from git import Repo, GitCommandError

def check_repo_status(repo_path="."):
    try:
        repo = Repo(repo_path)
    except Exception as e:
        print(f"Error: Could not open the repository at '{repo_path}'. Please check that the directory exists and is a valid git repository.\nDetails: {e}")
        sys.exit(1)

    if repo.bare:
        print("Repository is bare.")
        sys.exit(1)

    # Get current branch
    try:
        branch = repo.active_branch
    except TypeError:
        print("Detached HEAD state. Please checkout a branch.")
        sys.exit(1)

    remote_name = 'origin'
    remote_branch = f'{remote_name}/{branch.name}'

    # Fetch latest from remote
    try:
        repo.remotes[remote_name].fetch()
    except IndexError:
        available_remotes = [r.name for r in repo.remotes]
        if available_remotes:
            print(f"Error: Remote '{remote_name}' not found. Available remotes: {available_remotes}")
        else:
            print(f"Error: No git remotes found in this repository. Please add a remote named '{remote_name}' or specify an existing one.")
        sys.exit(1)
    except GitCommandError as e:
        print(f"Failed to fetch from remote: {e}")
        sys.exit(1)

    # Get commit objects
    local_commit = repo.commit(branch.name)
    try:
        remote_commit = repo.commit(remote_branch)
    except Exception:
        print(f"Remote branch {remote_branch} not found.")
        sys.exit(1)

    # Calculate ahead/behind
    ahead = sum(1 for _ in repo.iter_commits(f'{remote_branch}..{branch.name}'))
    behind = sum(1 for _ in repo.iter_commits(f'{branch.name}..{remote_branch}'))

    if ahead == 0 and behind == 0:
        print(f"Your branch '{branch.name}' is up to date with '{remote_branch}'.")
    elif ahead > 0 and behind == 0:
        print(f"Your branch '{branch.name}' is ahead of '{remote_branch}' by {ahead} commit(s). You may want to push.")
    elif ahead == 0 and behind > 0:
        print(f"Your branch '{branch.name}' is behind '{remote_branch}' by {behind} commit(s). You may want to pull.")
    else:
        print(f"Your branch and '{remote_branch}' have diverged. Local is ahead by {ahead} and behind by {behind} commit(s). Consider merging or rebasing.")

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