import argparse
import os
from . import check_repo_status

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if your local git repo is ahead, behind, or diverged from remote.")
    parser.add_argument("repo_path", nargs="?", default=".", help="Path to the git repository (default: current directory)")
    args = parser.parse_args()

    if not os.path.exists(args.repo_path):
        print(f"Error: Path '{args.repo_path}' does not exist.")
        exit(1)
    if not os.path.isdir(args.repo_path):
        print(f"Error: Path '{args.repo_path}' is not a directory.")
        exit(1)
    if not os.path.exists(os.path.join(args.repo_path, '.git')):
        print(f"Error: Path '{args.repo_path}' is not a git repository (missing .git directory).")
        exit(1)

    check_repo_status(args.repo_path) 