# Git-Pull-Indep

A tool to perform git pull independently. This Python script can be called from command line to perform git operations on a repository, including pull and submodule updates.

## Features

- Perform `git pull` on a specified repository
- Update submodules recursively with `git submodule update --init --recursive`
- Optional branch checkout before pulling (creates branch if it doesn't exist)
- **Automatic stash handling**: Automatically stashes uncommitted changes before pull and restores them after
- Cache path option to copy the project before execution (useful when used as a submodule)
- Initiator option to execute a Python script after completion using `os.execl` (useful for restarting the calling script after update)
- Uses `os.execl` for cache execution to replace the process (important when the project itself is being updated)
- Uses `sys.executable` for Python execution (venv compatible)
- Creates status marker file for success/failure tracking with detailed commit information
- Comprehensive logging

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python git_pull_indep.py /path/to/repo
```

### With Branch Checkout

```bash
python git_pull_indep.py /path/to/repo --checkout branch-name
```

If the branch doesn't exist locally, it will:
1. Check if it exists on the remote and create a tracking branch
2. If not on remote, create a new local branch

### With Cache Path

```bash
python git_pull_indep.py /path/to/repo --cache_path /tmp/cache
```

This is useful when the script is used as a submodule. The script will:
1. Copy itself to the cache path
2. Use `os.execl` to replace the current process and execute from the cache location
3. Perform the git operations

**Note**: The script uses `os.execl` instead of `subprocess` because the project itself might be updated during execution. This ensures the running script won't be affected by changes to its own files.

### With Initiator

```bash
python git_pull_indep.py /path/to/repo --initiator /path/to/caller_script.py
```

The `--initiator` option specifies a Python script to execute after the git operations complete successfully. The script uses `os.execl` to replace the current process with the initiator script.

**Use case**: When your application needs to update itself via git, you can use this option to restart your application after the update:
1. Your application calls `git_pull_indep.py` with `--initiator` pointing to your application's main script
2. Git operations complete successfully
3. The script executes your application using `os.execl`, effectively restarting it with the updated code

### All Options

```bash
python git_pull_indep.py /path/to/repo --checkout main --cache_path /tmp/cache --initiator /path/to/caller_script.py --log-level DEBUG
```

## Options

- `repo_path` (required): Path to the git repository
- `--checkout BRANCH`: Branch to checkout before pulling
- `--cache_path PATH`: Path to copy the project before execution (uses `os.execl` to replace process)
- `--initiator PATH`: Python script to execute after completion using `os.execl` (for restarting applications)
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO

## Status Tracking

After execution, the script creates two files in the repository:

1. `.git_pull_indep_status`: Contains execution status (SUCCESS/FAILURE), timestamp, repository change indicator, message, and detailed commit information
2. `.git_pull_indep.log`: Complete execution log

Example status file:
```
Status: SUCCESS
Timestamp: 2025-11-12T16:02:13.080804
Repository Changed: No
Message: All operations completed successfully

Current Commit:
Hash: e117850
Title: Add main file and submodule

Submodules Updated: Yes

Stash Status: Changes were stashed and restored
```

The "Repository Changed" field indicates whether the git pull operation retrieved any new changes:
- `Yes`: New commits were pulled from the remote
- `No`: Repository was already up-to-date or no remote configured

The "Current Commit" section provides the commit hash and title (first line of commit message) of the current HEAD after the pull operation.

The "Submodules Updated" field appears when submodules are present and have been updated.

The "Stash Status" field appears when uncommitted changes were automatically stashed and restored during the pull operation.

## Handling Uncommitted Changes

The script automatically handles uncommitted changes in the repository:

1. **Before pull**: If the repository has uncommitted changes (tracked modifications or untracked files), they are automatically stashed using `git stash push -u -m "git_pull_indep automatic stash"`
2. **After pull**: The stashed changes are automatically restored using `git stash pop`
3. **Conflict handling**: If conflicts occur when restoring stashed changes, the script logs a warning and leaves the changes in the stash for manual resolution

This ensures that:
- Git pull operations won't fail due to uncommitted changes
- Your local work is preserved and automatically restored
- You can resolve conflicts manually if they occur during stash restoration

Example log output with stash handling:
```
2025-11-12 15:29:16,358 - WARNING - Repository has uncommitted changes
2025-11-12 15:29:16,362 - INFO - Repository has uncommitted changes, stashing them
2025-11-12 15:29:16,374 - INFO - Changes stashed successfully
2025-11-12 15:29:16,374 - INFO - Performing git pull
2025-11-12 15:29:16,395 - INFO - Git pull completed successfully - Repository was updated
2025-11-12 15:29:16,395 - INFO - Restoring stashed changes
2025-11-12 15:29:16,404 - INFO - Stashed changes restored successfully
```

## Use Case: As a Submodule

When this tool is used as a submodule in a repository that needs to update itself:

1. The calling script invokes this script with `--cache_path` and `--initiator`
2. The script copies itself to the cache location
3. Uses `os.execl` to replace the current process and execute from cache (this prevents issues when the project files are updated)
4. Updates the parent repository
5. Uses `os.execl` to execute the initiator script, effectively restarting the calling application with updated code

Example from a calling script:
```python
import sys
import os

# Get paths
repo_path = "/path/to/repo"
script_path = "/path/to/git_pull_indep.py"
this_script = __file__  # The calling script itself

# Execute with os.system
# After git operations complete, this script will be executed again via os.execl
os.system(f"{sys.executable} {script_path} {repo_path} --cache_path /tmp/cache --initiator {this_script}")

# This line won't be reached if the update succeeds and initiator is executed
```

At the beginning of your application, check the status file:
```python
from pathlib import Path

repo_path = Path("/path/to/repo")
status_file = repo_path / ".git_pull_indep_status"

if status_file.exists():
    content = status_file.read_text()
    if "Status: SUCCESS" in content:
        print("Repository was updated successfully!")
        # Continue with updated code
    else:
        print("Repository update failed!")
        # Handle error
```
```

## Requirements

- Python 3.6+
- GitPython 3.1.0+

## License

See LICENSE file.
