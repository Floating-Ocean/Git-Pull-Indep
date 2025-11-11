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
2. Execute from the cache location
3. Perform all git operations on the target repo
4. This prevents conflicts when the script itself is part of the repo being updated

## Example 4: All Options

```bash
$ python git_pull_indep.py /path/to/repo \
    --checkout main \
    --cache_path /tmp/cache \
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

```python
import sys
import subprocess

# Get the current Python interpreter (works in venv)
python_exe = sys.executable

# Path to the git-pull-indep script
script_path = "/path/to/git_pull_indep.py"

# Repository to update
repo_path = "/path/to/repo"

# Execute the script
result = subprocess.run(
    [python_exe, script_path, repo_path, "--checkout", "main"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("Update successful!")
else:
    print(f"Update failed: {result.stderr}")
```
