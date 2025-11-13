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
Timestamp: 2025-11-12T16:27:39.583792
Repository Changed: Yes (with stashes)
Submodule Updates: mysub, othersub

Current Commit:
Hash: 18b7abc966f77f46520e6a91e76063fd8d86ac6f
Title: Update from remote
Branch: master
```

The status file shows:
- Repository Changed: "No", "Yes", or "Yes (with stashes)"
- Submodule Updates: "None" or comma-separated list of updated submodules
- Current Commit: Full hash, title, and branch name

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

## Example 6: Handling Uncommitted Changes

When your repository has uncommitted changes, the script automatically stashes them before pulling:

```bash
$ cd /path/to/repo
$ echo "local change" > file.txt  # Make some uncommitted changes
$ python git_pull_indep.py /path/to/repo
```

Output:
```
2025-11-12 16:27:39,544 - WARNING - Repository has uncommitted changes
2025-11-12 16:27:39,550 - INFO - Repository has uncommitted changes, stashing them
2025-11-12 16:27:39,562 - INFO - Changes stashed successfully
2025-11-12 16:27:39,562 - INFO - Performing git pull
2025-11-12 16:27:39,583 - INFO - Git pull completed successfully - Repository was updated
2025-11-12 16:27:39,583 - INFO - Updating submodules
2025-11-12 16:27:39,583 - INFO - No submodules found
```

The script:
1. Detects uncommitted changes (both tracked and untracked files)
2. Stashes them automatically with `git stash push -u`
3. Performs the pull operation
4. **Leaves changes in stash** - use `git stash pop` to restore them manually

To restore your changes after reviewing the pulled updates:
```bash
$ git stash pop
```

## Checking Status Programmatically

```python
import sys
from pathlib import Path
import re

repo_path = Path("/path/to/repo")
status_file = repo_path / ".git_pull_indep_status"

if status_file.exists():
    content = status_file.read_text()
    if "Status: SUCCESS" in content:
        print("Git pull succeeded!")
        
        # Check if repository had changes
        if "Repository Changed: Yes (with stashes)" in content:
            print("Repository was updated with new changes and stashes were created!")
            print("Use 'git stash pop' to restore your uncommitted changes")
        elif "Repository Changed: Yes" in content:
            print("Repository was updated with new changes!")
            # Application may need to reload or restart
        else:
            print("Repository was already up-to-date.")
        
        # Extract commit information
        if "Hash:" in content:
            hash_match = re.search(r"Hash: ([a-f0-9]+)", content)
            title_match = re.search(r"Title: (.+)", content)
            branch_match = re.search(r"Branch: (.+)", content)
            if hash_match and title_match:
                print(f"Current commit: {hash_match.group(1)[:7]}")
                print(f"Commit title: {title_match.group(1)}")
                if branch_match:
                    print(f"Branch: {branch_match.group(1)}")
        
        # Check for submodule updates
        submodule_match = re.search(r"Submodule Updates: (.+)", content)
        if submodule_match and submodule_match.group(1) != "None":
            print(f"Submodules updated: {submodule_match.group(1)}")
        
        # Continue with your application
    else:
        print("Git pull failed!")
        # Handle failure
        sys.exit(1)
```
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
