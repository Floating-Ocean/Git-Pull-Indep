# Git-Pull-Indep

A tool to perform git pull independently. This Python script can be called from command line to perform git operations on a repository, including pull and submodule updates.

## Features

- Perform `git pull` on a specified repository
- Update submodules recursively with `git submodule update --init --recursive`
- Optional branch checkout before pulling (creates branch if it doesn't exist)
- Cache path option to copy the project before execution (useful when used as a submodule)
- Uses `sys.executable` for Python execution (venv compatible)
- Automatically returns to the caller's directory after operations
- Creates status marker file for success/failure tracking
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
2. Execute from the cache location
3. Perform the git operations

### All Options

```bash
python git_pull_indep.py /path/to/repo --checkout main --cache_path /tmp/cache --log-level DEBUG
```

## Options

- `repo_path` (required): Path to the git repository
- `--checkout BRANCH`: Branch to checkout before pulling
- `--cache_path PATH`: Path to copy the project before execution
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO

## Status Tracking

After execution, the script creates two files in the repository:

1. `.git_pull_indep_status`: Contains execution status (SUCCESS/FAILURE), timestamp, and message
2. `.git_pull_indep.log`: Complete execution log

Example status file:
```
Status: SUCCESS
Timestamp: 2025-11-11T07:28:48.964700
Message: All operations completed successfully
```

## Use Case: As a Submodule

When this tool is used as a submodule in a repository that needs to update itself:

1. The calling script invokes this script with `--cache_path`
2. The script copies itself to the cache location
3. Executes from cache to avoid conflicts with the repository being updated
4. Updates the parent repository
5. After restart, the calling script can check the status file to confirm success

## Requirements

- Python 3.6+
- GitPython 3.1.0+

## License

See LICENSE file.
