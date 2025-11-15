#!/usr/bin/env python3
"""
Git Pull Independent Script

This script performs git pull and submodule updates on a given repository.
It can be called from command line and supports:
- Branch checkout before pulling (with creation if needed)
- Cache path to copy the script to a different location before execution
- Status markers and logging for monitoring
"""

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

try:
    import git
except ImportError:
    print("GitPython is required. Install it with: pip install gitpython")
    sys.exit(1)


class GitPullIndep:
    """Main class for git pull operations"""
    
    def __init__(self, repo_path, checkout_branch=None, cache_path=None, initiator=None, log_level="INFO"):
        self.repo_path = Path(repo_path).resolve()
        self.checkout_branch = checkout_branch
        self.cache_path = Path(cache_path).resolve() if cache_path else None
        self.initiator = Path(initiator).resolve() if initiator else None
        self.original_dir = Path.cwd()
        self.status_file = self.repo_path / ".git_pull_indep_status"
        self.log_file = self.repo_path / ".git_pull_indep.log"
        self.repo_changed = False  # Track if repo had changes
        self.stashed = False  # Track if we stashed changes
        self.updated_submodules = []  # Track list of updated submodules
        
        # Setup logging
        self._setup_logging(log_level)
        
    def _setup_logging(self, log_level):
        """Setup logging configuration"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _write_status(self, success, message="", repo=None):
        """Write status to status file"""
        status = "SUCCESS" if success else "FAILURE"
        timestamp = datetime.now().isoformat()
        
        with open(self.status_file, 'w', encoding='utf-8') as f:
            f.write(f"Status: {status}\n")
            f.write(f"Timestamp: {timestamp}\n")
            
            # For SUCCESS status, add Repository Changed and Submodule Updates
            if success:
                # Determine Repository Changed status
                if self.stashed:
                    repo_status = "Yes (with stashes)"
                elif self.repo_changed:
                    repo_status = "Yes"
                else:
                    repo_status = "No"
                f.write(f"Repository Changed: {repo_status}\n")
                
                # Add submodule updates - only include modules that were actually updated
                if self.updated_submodules:
                    submodule_list = ", ".join(self.updated_submodules)
                    f.write(f"Submodule Updates: {submodule_list}\n")
                else:
                    f.write(f"Submodule Updates: None\n")
            
            # Add commit information if repo is available
            if repo:
                try:
                    current_commit = repo.head.commit
                    commit_title = current_commit.message.strip().split('\n')[0]
                    # Get branch name
                    try:
                        branch_name = repo.active_branch.name
                    except:
                        # Handle detached HEAD state
                        branch_name = "(detached)"
                    f.write(f"\nCurrent Commit:\n")
                    f.write(f"{current_commit.hexsha} ({branch_name})\n")
                    f.write(f"{commit_title}\n")
                except Exception as e:
                    self.logger.warning(f"Could not retrieve commit information: {e}")
        
        self.logger.info(f"Status written: {status}")
        
    def _copy_to_cache(self):
        """Copy the project to cache path and return the new script path"""
        if not self.cache_path:
            return None
            
        try:
            self.logger.info(f"Copying project to cache path: {self.cache_path}")
            
            # Create cache directory if it doesn't exist
            self.cache_path.mkdir(parents=True, exist_ok=True)
            
            # Get the current script's parent directory (project root)
            project_root = Path(__file__).parent.resolve()
            
            # Copy the entire project to cache
            cache_project_path = self.cache_path / project_root.name
            
            # Remove old cache if exists
            if cache_project_path.exists():
                shutil.rmtree(cache_project_path)
            
            shutil.copytree(project_root, cache_project_path)
            
            # Return the path to the script in cache
            cached_script = cache_project_path / Path(__file__).name
            self.logger.info(f"Project copied to: {cache_project_path}")
            
            return cached_script
            
        except Exception as e:
            self.logger.error(f"Failed to copy to cache: {e}")
            raise
    
    def _checkout_branch(self, repo):
        """Checkout the specified branch, create if doesn't exist"""
        if not self.checkout_branch:
            return
            
        try:
            self.logger.info(f"Checking out branch: {self.checkout_branch}")
            
            # Check if branch exists locally
            branch_exists = False
            for branch in repo.heads:
                if branch.name == self.checkout_branch:
                    branch_exists = True
                    break
            
            if branch_exists:
                # Branch exists, checkout
                self.logger.info(f"Branch {self.checkout_branch} exists, checking out")
                repo.git.checkout(self.checkout_branch)
            else:
                # Check if branch exists on remote
                remote_branch_exists = False
                try:
                    repo.git.fetch()
                    for ref in repo.remote().refs:
                        if ref.name == f"origin/{self.checkout_branch}":
                            remote_branch_exists = True
                            break
                except Exception as e:
                    self.logger.warning(f"Failed to fetch remote: {e}")
                
                if remote_branch_exists:
                    # Branch exists on remote, checkout and track
                    self.logger.info(f"Branch {self.checkout_branch} exists on remote, creating local tracking branch")
                    repo.git.checkout('-b', self.checkout_branch, f'origin/{self.checkout_branch}')
                else:
                    # Branch doesn't exist, create new
                    self.logger.info(f"Branch {self.checkout_branch} doesn't exist, creating new branch")
                    repo.git.checkout('-b', self.checkout_branch)
            
            self.logger.info(f"Successfully checked out branch: {self.checkout_branch}")
            
        except Exception as e:
            self.logger.error(f"Failed to checkout branch: {e}")
            raise
    
    def _stash_changes(self, repo):
        """Stash uncommitted changes if repository is dirty"""
        try:
            if repo.is_dirty(untracked_files=True):
                self.logger.info("Repository has uncommitted changes, stashing them")
                try:
                    repo.git.stash('push', '-u', '-m', 'git_pull_indep automatic stash')
                    self.stashed = True
                    self.logger.info("Changes stashed successfully")
                except git.exc.GitCommandError as e:
                    self.logger.error(f"Failed to stash changes (git command error): {e}")
                    self.logger.warning("Continuing without stashing - pull may fail if there are conflicts")
                except Exception as e:
                    self.logger.error(f"Failed to stash changes (unexpected error): {e}")
                    self.logger.warning("Continuing without stashing - pull may fail if there are conflicts")
            else:
                self.logger.info("Repository is clean, no need to stash")
        except Exception as e:
            self.logger.error(f"Failed to check repository status: {e}")
            raise
    
    def _pop_stash(self, repo):
        """Pop stashed changes back to working directory"""
        try:
            self.logger.info("Attempting to pop stashed changes")
            try:
                repo.git.stash('pop')
                self.stashed = False  # Reset stashed flag since we've restored the changes
                self.logger.info("Stashed changes restored successfully")
            except git.exc.GitCommandError as e:
                self.logger.error(f"Failed to pop stash (git command error): {e}")
                self.logger.warning("Stashed changes remain in stash - you may need to manually resolve with 'git stash pop'")
            except Exception as e:
                self.logger.error(f"Failed to pop stash (unexpected error): {e}")
                self.logger.warning("Stashed changes remain in stash - you may need to manually resolve with 'git stash pop'")
        except Exception as e:
            self.logger.error(f"Unexpected error in pop stash operation: {e}")
            # Don't raise - we want to continue even if pop fails

    
    def _git_pull(self, repo):
        """Perform git pull operation"""
        try:
            self.logger.info("Performing git pull")
            
            # Check if remote 'origin' exists
            if 'origin' not in [remote.name for remote in repo.remotes]:
                self.logger.warning("No 'origin' remote configured, skipping git pull")
                return
            
            origin = repo.remote(name='origin')
            pull_info = origin.pull()
            
            for info in pull_info:
                self.logger.info(f"Pulled: {info.ref} - {info.flags}")
                # Check if HEAD_UPTODATE flag (4) is not set, meaning changes were pulled
                # HEAD_UPTODATE = 4 means no changes
                if info.flags != 4:
                    self.repo_changed = True
            
            if self.repo_changed:
                self.logger.info("Git pull completed successfully - Repository was updated")
            else:
                self.logger.info("Git pull completed successfully - Repository already up-to-date")
            
        except Exception as e:
            self.logger.error(f"Failed to perform git pull: {e}")
            raise
    
    def _update_submodules(self, repo):
        """Update submodules recursively"""
        try:
            self.logger.info("Updating submodules")
            
            # Initialize and update submodules recursively
            if repo.submodules:
                # Track submodule commit SHAs before update
                submodule_shas_before = {}
                for submodule in repo.submodules:
                    try:
                        # Get the current HEAD of the submodule directory (not what parent expects)
                        submodule_repo = git.Repo(submodule.abspath)
                        submodule_shas_before[submodule.name] = submodule_repo.head.commit.hexsha
                    except Exception as e:
                        self.logger.warning(f"Could not get SHA for submodule {submodule.name}: {e}")
                        # If we can't get the SHA, assume it needs updating
                        submodule_shas_before[submodule.name] = None
                
                # Perform the update
                repo.git.submodule('update', '--init', '--recursive')
                
                # Check which submodules were actually updated
                for submodule in repo.submodules:
                    try:
                        # Refresh the submodule to get current state
                        submodule_repo = git.Repo(submodule.abspath)
                        current_sha = submodule_repo.head.commit.hexsha
                        old_sha = submodule_shas_before.get(submodule.name)
                        
                        # Only add to updated list if SHA changed
                        if old_sha != current_sha:
                            self.logger.info(f"Submodule {submodule.name} was updated: {old_sha[:7] if old_sha else 'N/A'} -> {current_sha[:7]}")
                            self.updated_submodules.append(submodule.name)
                        else:
                            self.logger.info(f"Submodule {submodule.name} is already up-to-date")
                    except Exception as e:
                        self.logger.warning(f"Could not check update status for submodule {submodule.name}: {e}")
                        # If we can't verify, assume it was updated to be safe
                        if submodule.name not in self.updated_submodules:
                            self.updated_submodules.append(submodule.name)
                
                if self.updated_submodules:
                    self.logger.info(f"Submodules updated successfully: {', '.join(self.updated_submodules)}")
                else:
                    self.logger.info("Submodules checked - all already up-to-date")
            else:
                self.logger.info("No submodules found")
                
        except Exception as e:
            self.logger.error(f"Failed to update submodules: {e}")
            raise
    
    def run(self):
        """Main execution method"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("Git Pull Independent Script Started")
            self.logger.info(f"Repository: {self.repo_path}")
            self.logger.info(f"Original directory: {self.original_dir}")
            
            # Check if we need to copy to cache and re-execute
            if self.cache_path and not os.environ.get('GIT_PULL_INDEP_FROM_CACHE'):
                cached_script = self._copy_to_cache()
                
                if cached_script:
                    self.logger.info("Re-executing from cache location using os.execl")
                    
                    # Build arguments for re-execution from cache
                    args = [
                        sys.executable,
                        str(cached_script),
                        str(self.repo_path)
                    ]
                    
                    if self.checkout_branch:
                        args.extend(['--checkout', self.checkout_branch])
                    
                    if self.initiator:
                        args.extend(['--initiator', str(self.initiator)])
                    
                    # Set environment variable to prevent infinite loop
                    # Store the cache path for verification
                    os.environ['GIT_PULL_INDEP_FROM_CACHE'] = str(self.cache_path)
                    
                    # Execute from cache using os.execl (replaces current process)
                    # This is important because the project itself might be updated
                    self.logger.info(f"Executing: {' '.join(args)}")
                    os.execl(sys.executable, *args)
                    # Code after os.execl will not be reached
                    return
            elif 'GIT_PULL_INDEP_FROM_CACHE' in os.environ:
                # Clean up the environment variable immediately after detecting it
                # This prevents it from persisting if an exception occurs or user exits
                cached_from = os.environ['GIT_PULL_INDEP_FROM_CACHE']
                del os.environ['GIT_PULL_INDEP_FROM_CACHE']
                self.logger.info(f"Cleaned up GIT_PULL_INDEP_FROM_CACHE environment variable (was: {cached_from})")
                
                # Verify we're running from the expected cache location
                current_script = Path(__file__).parent.resolve()
                expected_cache_location = Path(cached_from) / current_script.name
                if current_script == expected_cache_location:
                    self.logger.info(f"Verified: Running from cache location: {current_script}")
                else:
                    error_msg = f"Cache location mismatch: expected {expected_cache_location}, running from {current_script}"
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)
            
            # Validate repository path
            if not self.repo_path.exists():
                raise ValueError(f"Repository path does not exist: {self.repo_path}")
            
            if not (self.repo_path / ".git").exists():
                raise ValueError(f"Not a git repository: {self.repo_path}")
            
            # Open the repository
            self.logger.info("Opening repository")
            repo = git.Repo(self.repo_path)
            
            # Check for uncommitted changes and stash if needed
            if repo.is_dirty(untracked_files=True):
                self.logger.warning("Repository has uncommitted changes")
                self._stash_changes(repo)
            
            # Perform operations
            self._checkout_branch(repo)
            self._git_pull(repo)
            self._update_submodules(repo)
            
            # If no changes were pulled and we stashed changes, pop them back
            if not self.repo_changed and self.stashed:
                self.logger.info("No remote changes were pulled, restoring stashed local changes")
                self._pop_stash(repo)
            
            # Write success status with commit information
            self._write_status(True, "All operations completed successfully", repo)
            
            if self.repo_changed:
                self.logger.info("All operations completed successfully - Repository was updated with new changes")
            else:
                self.logger.info("All operations completed successfully - Repository was already up-to-date")
            self.logger.info("=" * 60)
            
            # If initiator is provided, execute it using os.execl
            if self.initiator:
                self.logger.info(f"Switching back to initiator: os.execl -> python {self.initiator}")
                # Use os.execl to replace current process with the initiator
                os.execl(sys.executable, sys.executable, str(self.initiator))
                # Code after os.execl will not be reached
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.logger.error(error_msg)
            # Try to get repo for failure status, but handle if it doesn't exist
            try:
                repo = git.Repo(self.repo_path) if self.repo_path.exists() and (self.repo_path / ".git").exists() else None
            except:
                repo = None
            self._write_status(False, "", repo)
            
            # If initiator is provided, execute it even after exception
            # This allows the initiator to handle the failure appropriately
            if self.initiator:
                self.logger.info(f"Exception occurred, but switching back to initiator: os.execl -> python {self.initiator}")
                # Use os.execl to replace current process with the initiator
                os.execl(sys.executable, sys.executable, str(self.initiator))
                # Code after os.execl will not be reached
            
            # If no initiator, re-raise the exception
            raise
        
        finally:
            # Only change directory if we're not executing initiator
            # (if initiator is set, we won't reach here because of os.execl)
            if not self.initiator:
                os.chdir(self.original_dir)
                self.logger.info(f"Returned to original directory: {self.original_dir}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Git Pull Independent Script - Perform git pull and submodule updates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/repo
  %(prog)s /path/to/repo --checkout main
  %(prog)s /path/to/repo --checkout feature-branch --cache_path /tmp/cache
  %(prog)s /path/to/repo --initiator /path/to/caller_script.py
        """
    )
    
    parser.add_argument(
        'repo_path',
        help='Path to the git repository'
    )
    
    parser.add_argument(
        '--checkout',
        dest='checkout_branch',
        help='Branch to checkout before pulling (will be created if doesn\'t exist)'
    )
    
    parser.add_argument(
        '--cache_path',
        help='Path to copy the project before execution (for submodule scenarios)'
    )
    
    parser.add_argument(
        '--initiator',
        help='Path to the Python script to execute after completion (using os.execl)'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    try:
        git_pull = GitPullIndep(
            repo_path=args.repo_path,
            checkout_branch=args.checkout_branch,
            cache_path=args.cache_path,
            initiator=args.initiator,
            log_level=args.log_level
        )
        git_pull.run()
        sys.exit(0)
        
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
