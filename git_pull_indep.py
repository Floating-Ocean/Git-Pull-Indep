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
        
    def _write_status(self, success, message=""):
        """Write status to status file"""
        status = "SUCCESS" if success else "FAILURE"
        timestamp = datetime.now().isoformat()
        
        with open(self.status_file, 'w') as f:
            f.write(f"Status: {status}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Message: {message}\n")
        
        self.logger.info(f"Status written: {status} - {message}")
        
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
            
            self.logger.info("Git pull completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to perform git pull: {e}")
            raise
    
    def _update_submodules(self, repo):
        """Update submodules recursively"""
        try:
            self.logger.info("Updating submodules")
            
            # Initialize and update submodules recursively
            if repo.submodules:
                for submodule in repo.submodules:
                    self.logger.info(f"Updating submodule: {submodule.name}")
                
                repo.git.submodule('update', '--init', '--recursive')
                self.logger.info("Submodules updated successfully")
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
                    os.environ['GIT_PULL_INDEP_FROM_CACHE'] = '1'
                    
                    # Execute from cache using os.execl (replaces current process)
                    # This is important because the project itself might be updated
                    self.logger.info(f"Executing: {' '.join(args)}")
                    os.execl(sys.executable, *args)
                    # Code after os.execl will not be reached
                    return
            
            # Validate repository path
            if not self.repo_path.exists():
                raise ValueError(f"Repository path does not exist: {self.repo_path}")
            
            if not (self.repo_path / ".git").exists():
                raise ValueError(f"Not a git repository: {self.repo_path}")
            
            # Open the repository
            self.logger.info("Opening repository")
            repo = git.Repo(self.repo_path)
            
            # Check for uncommitted changes
            if repo.is_dirty():
                self.logger.warning("Repository has uncommitted changes")
            
            # Perform operations
            self._checkout_branch(repo)
            self._git_pull(repo)
            self._update_submodules(repo)
            
            # Write success status
            self._write_status(True, "All operations completed successfully")
            
            self.logger.info("All operations completed successfully")
            self.logger.info("=" * 60)
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.logger.error(error_msg)
            self._write_status(False, error_msg)
            raise
        
        finally:
            # Return to initiator directory if provided, otherwise original directory
            target_dir = self.initiator if self.initiator else self.original_dir
            os.chdir(target_dir)
            self.logger.info(f"Returned to directory: {target_dir}")


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
  %(prog)s /path/to/repo --initiator /path/to/caller/dir
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
        help='Path to the initiator directory to return to after execution'
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
