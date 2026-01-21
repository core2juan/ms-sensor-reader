import logging
import subprocess
import threading
import sys
import os
import signal
import time
from github import Github, GithubIntegration
from common.settings import Settings

logger = logging.getLogger(__name__)

def _log_and_flush(message, level="info"):
    getattr(logger, level)(message)
    sys.stdout.flush()

class RepoRefresher:
    _instance = None
    restart_requested = False
    _github_token = None
    _token_expiry = 0

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.settings = Settings()
            cls.restart_requested = False
            cls._github_token = None
            cls._token_expiry = 0
            if cls.settings.repo_refresher_enabled:
                cls._instance._start_refresh_thread()
            else:
                _log_and_flush("RepoRefresher disabled in settings")
        return cls._instance

    def _start_refresh_thread(self):
        self._stop = threading.Event()
        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._refresh_thread.start()
        _log_and_flush(f"RepoRefresher started, checking every {self.settings.repo_check_interval_minutes} minutes")

    def _get_github_token(self):
        """Get GitHub installation access token, using cached token if still valid."""
        if self._github_token and time.time() < self._token_expiry:
            return self._github_token
        
        try:
            if not self.settings.github_app_id or not self.settings.github_app_pem_path:
                _log_and_flush("GitHub App credentials not configured, skipping auth", "warning")
                return None
            
            with open(self.settings.github_app_pem_path, 'r') as pem_file:
                private_key = pem_file.read()
            
            integration = GithubIntegration(self.settings.github_app_id, private_key)
            
            installation = integration.get_installations()[0]
            installation_id = installation.id
            
            token = integration.get_access_token(installation_id).token
            
            self._github_token = token
            self._token_expiry = time.time() + (50 * 60)  # Cache for 50 minutes
            
            _log_and_flush("GitHub App token obtained successfully")
            return token
            
        except FileNotFoundError:
            _log_and_flush(f"PEM file not found at {self.settings.github_app_pem_path}", "error")
            return None
        except Exception as e:
            _log_and_flush(f"Failed to get GitHub token: {e}", "error")
            return None

    def _setup_git_auth(self, repo_path):
        """Configure git remote with GitHub App token for HTTPS authentication."""
        token = self._get_github_token()
        if not token:
            _log_and_flush("No GitHub token available, using existing remote", "warning")
            return False
        
        try:
            if not self.settings.github_repo_owner or not self.settings.github_repo_name:
                _log_and_flush("GitHub repo owner/name not configured", "warning")
                return False
            
            auth_url = f"https://x-access-token:{token}@github.com/{self.settings.github_repo_owner}/{self.settings.github_repo_name}.git"
            
            result = subprocess.run(
                ["git", "remote", "set-url", "origin", auth_url],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                _log_and_flush(f"Failed to set git remote URL: {result.stderr}", "error")
                return False
            
            return True
            
        except Exception as e:
            _log_and_flush(f"Error setting up git auth: {e}", "error")
            return False

    def _cleanup_git_auth(self, repo_path, original_url=None):
        """Remove token from git remote URL for security."""
        try:
            if original_url:
                subprocess.run(
                    ["git", "remote", "set-url", "origin", original_url],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                clean_url = f"https://github.com/{self.settings.github_repo_owner}/{self.settings.github_repo_name}.git"
                subprocess.run(
                    ["git", "remote", "set-url", "origin", clean_url],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
        except Exception as e:
            _log_and_flush(f"Warning: Failed to cleanup git auth: {e}", "warning")

    def _refresh_loop(self):
        while not self._stop.is_set():
            self._check_and_update()
            self._stop.wait(self.settings.repo_check_interval_minutes * 60)

    def _check_and_update(self):
        try:
            _log_and_flush("Checking for repository updates...")
            
            repo_path = os.path.dirname(os.path.dirname(__file__))
            
            # Setup GitHub App authentication
            self._setup_git_auth(repo_path)
            
            result = subprocess.run(
                ["git", "fetch", "origin", self.settings.repo_branch],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                _log_and_flush(f"Failed to fetch from origin: {result.stderr}", "error")
                self._cleanup_git_auth(repo_path)
                return
            
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                _log_and_flush(f"Failed to get local commit: {result.stderr}", "error")
                return
            
            local_commit = result.stdout.strip()
            
            result = subprocess.run(
                ["git", "rev-parse", f"origin/{self.settings.repo_branch}"],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                _log_and_flush(f"Failed to get remote commit: {result.stderr}", "error")
                return
            
            remote_commit = result.stdout.strip()
            
            if local_commit != remote_commit:
                _log_and_flush(f"Updates available: {local_commit[:7]} -> {remote_commit[:7]}")
                self._update_and_restart()
            else:
                _log_and_flush(f"Repository is up to date (commit: {local_commit[:7]})")
            
            # Cleanup git auth after operations
            self._cleanup_git_auth(repo_path)
                
        except subprocess.TimeoutExpired as e:
            _log_and_flush(f"Git command timed out: {e}", "error")
            self._cleanup_git_auth(os.path.dirname(os.path.dirname(__file__)))
        except Exception as e:
            _log_and_flush(f"Error checking for updates: {e}", "error")
            self._cleanup_git_auth(os.path.dirname(os.path.dirname(__file__)))

    def _update_and_restart(self):
        repo_path = os.path.dirname(os.path.dirname(__file__))
        try:
            _log_and_flush("Pulling latest changes...")
            
            # Setup GitHub App authentication (already done in _check_and_update, but ensure it's set)
            self._setup_git_auth(repo_path)
            
            result = subprocess.run(
                ["git", "pull", "origin", self.settings.repo_branch],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                _log_and_flush(f"Failed to pull changes: {result.stderr}", "error")
                self._cleanup_git_auth(repo_path)
                return
            
            _log_and_flush("Installing dependencies with poetry...")
            result = subprocess.run(
                ["poetry", "install"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                _log_and_flush(f"Failed to install dependencies: {result.stderr}", "error")
                self._cleanup_git_auth(repo_path)
                return
            
            # Cleanup git auth before restart
            self._cleanup_git_auth(repo_path)
            
            _log_and_flush("Restarting application...")
            _log_and_flush("Initiating graceful shutdown...")
            
            RepoRefresher.restart_requested = True
            os.kill(os.getpid(), signal.SIGTERM)
            
        except subprocess.TimeoutExpired:
            _log_and_flush("Update command timed out", "error")
            self._cleanup_git_auth(repo_path)
        except Exception as e:
            _log_and_flush(f"Error during update and restart: {e}", "error")
            self._cleanup_git_auth(repo_path)