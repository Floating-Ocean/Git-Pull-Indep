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

## Example 4: With Initiator Script

```bash
$ python git_pull_indep.py /path/to/repo --initiator /path/to/caller_script.py
```

The script will:
1. Perform all git operations
2. Use `os.execl` to execute `/path/to/caller_script.py`, replacing the current process

This is useful when:
- Your application needs to restart itself after a git update
- The calling script should be executed with the updated code

**Example workflow**:
1. Your application detects it needs an update
2. It calls `git_pull_indep.py` with `--initiator __file__` (pointing to itself)
3. Git operations complete successfully
4. Your application is executed again via `os.execl`, now running the updated code

## Example 5: All Options

```bash
$ python git_pull_indep.py /path/to/repo \
    --checkout main \
    --cache_path /tmp/cache \
    --initiator /path/to/caller_script.py \
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

### Self-Updating Application

```python
import sys
import os

# Get the current Python interpreter (works in venv)
python_exe = sys.executable

# Path to the git-pull-indep script
script_path = "/path/to/git_pull_indep.py"

# Repository to update
repo_path = "/path/to/repo"

# This script itself - will be executed after update via os.execl
this_script = __file__

# Execute the update script
result = os.system(
    f"{python_exe} {script_path} {repo_path} "
    f"--checkout main --initiator {this_script}"
)

# This line won't be reached if update succeeds and initiator is executed
if result != 0:
    print("Update failed!")
```

### Advanced Approach (For scenarios where git_pull_indep is in repo being updated)

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

# This script - will be executed after update
this_script = __file__

# Execute with cache_path to prevent issues if script is part of repo being updated
result = os.system(
    f"{python_exe} {script_path} {repo_path} "
    f"--cache_path {cache_path} --initiator {this_script}"
)

# This line won't be reached if update succeeds and initiator is executed
if result != 0:
    print("Update failed!")
```
