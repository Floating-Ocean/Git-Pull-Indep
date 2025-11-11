# Usage Examples

## Example 1: Basic Usage

```bash
$ python git_pull_indep.py /path/to/repo
```

Output:
```
2025-11-11 07:33:46,630 - INFO - Git Pull Independent Script Started
2025-11-11 07:33:46,630 - INFO - Repository: /path/to/repo
2025-11-11 07:33:46,637 - INFO - Performing git pull
2025-11-11 07:33:46,648 - INFO - Pulled: origin/master - 4
2025-11-11 07:33:46,649 - INFO - Git pull completed successfully
2025-11-11 07:33:46,649 - INFO - Updating submodules
2025-11-11 07:33:46,653 - INFO - Updating submodule: mysub
2025-11-11 07:33:46,675 - INFO - Submodules updated successfully
2025-11-11 07:33:46,675 - INFO - All operations completed successfully
```

Status file (`.git_pull_indep_status`):
```
Status: SUCCESS
Timestamp: 2025-11-11T07:33:46.675123
Message: All operations completed successfully
```

## Example 2: With Branch Checkout

```bash
$ python git_pull_indep.py /path/to/repo --checkout feature-branch
```

The script will:
1. Check if `feature-branch` exists locally
2. If not, check if it exists on remote and create tracking branch
3. If not on remote either, create a new local branch
4. Checkout the branch
5. Perform git pull
6. Update submodules

## Example 3: With Cache Path (Submodule Scenario)

```bash
$ python git_pull_indep.py /path/to/repo --cache_path /tmp/cache
```

The script will:
1. Copy itself to `/tmp/cache/Git-Pull-Indep/`
2. Use `os.execl` to replace the current process and execute from the cache location
3. Perform all git operations on the target repo
4. This prevents conflicts when the script itself is part of the repo being updated

**Note**: The script uses `os.execl` instead of `subprocess` because the project might be updated during execution.

## Example 4: With Initiator Directory

```bash
$ python git_pull_indep.py /path/to/repo --initiator /path/to/caller/dir
```

The script will:
1. Perform all git operations
2. Return to `/path/to/caller/dir` instead of the original working directory

This is useful when:
- The calling script is in a different repository
- You want to ensure the script returns to a specific directory regardless of where it was called from

## Example 5: All Options

```bash
$ python git_pull_indep.py /path/to/repo \
    --checkout main \
    --cache_path /tmp/cache \
    --initiator /path/to/caller \
    --log-level DEBUG
```

## Checking Status Programmatically

```python
import sys
from pathlib import Path

repo_path = Path("/path/to/repo")
status_file = repo_path / ".git_pull_indep_status"

if status_file.exists():
    content = status_file.read_text()
    if "Status: SUCCESS" in content:
        print("Git pull succeeded!")
        # Continue with your application
    else:
        print("Git pull failed!")
        # Handle failure
        sys.exit(1)
```

## Calling from Another Python Script

### Simple Approach (Using os.system)

```python
import sys
import os
from pathlib import Path

# Get the current Python interpreter (works in venv)
python_exe = sys.executable

# Path to the git-pull-indep script
script_path = "/path/to/git_pull_indep.py"

# Repository to update
repo_path = "/path/to/repo"

# Current directory to return to
initiator_dir = os.getcwd()

# Execute the script
result = os.system(
    f"{python_exe} {script_path} {repo_path} "
    f"--checkout main --initiator {initiator_dir}"
)

if result == 0:
    print("Update successful!")
else:
    print("Update failed!")
```

### Advanced Approach (For scenarios where script might be updated)

```python
import sys
import os

# Get the current Python interpreter (works in venv)
python_exe = sys.executable

# Path to the git-pull-indep script (might be in the repo being updated)
script_path = "/path/to/repo/submodule/git_pull_indep.py"

# Repository to update (parent repo)
repo_path = "/path/to/repo"

# Cache path to avoid conflicts
cache_path = "/tmp/git_pull_cache"

# Current directory to return to
initiator_dir = os.getcwd()

# Execute with cache_path to prevent issues if script is part of repo being updated
result = os.system(
    f"{python_exe} {script_path} {repo_path} "
    f"--cache_path {cache_path} --initiator {initiator_dir}"
)

if result == 0:
    # Check status file for detailed info
    status_file = Path(repo_path) / ".git_pull_indep_status"
    if status_file.exists():
        print(status_file.read_text())
else:
    print("Update failed!")
```
