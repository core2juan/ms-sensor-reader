import logging
import subprocess
import threading
import sys
import os
import signal
from time import sleep
from common.settings import Settings

logger = logging.getLogger(__name__)

def _log_and_flush(message, level="info"):
    getattr(logger, level)(message)
    sys.stdout.flush()

class RepoRefresher:
    _instance = None
    restart_requested = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.settings = Settings()
            cls.restart_requested = False
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

    def _refresh_loop(self):
        while not self._stop.is_set():
            self._check_and_update()
            self._stop.wait(self.settings.repo_check_interval_minutes * 60)

    def _check_and_update(self):
        try:
            _log_and_flush("Checking for repository updates...")
            
            repo_path = os.path.dirname(os.path.dirname(__file__))
            
            result = subprocess.run(
                ["git", "fetch", "origin", self.settings.repo_branch],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                _log_and_flush(f"Failed to fetch from origin: {result.stderr}", "error")
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
                
        except subprocess.TimeoutExpired as e:
            _log_and_flush(f"Git command timed out: {e}", "error")
        except Exception as e:
            _log_and_flush(f"Error checking for updates: {e}", "error")

    def _update_and_restart(self):
        try:
            _log_and_flush("Pulling latest changes...")
            result = subprocess.run(
                ["git", "pull", "origin", self.settings.repo_branch],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                _log_and_flush(f"Failed to pull changes: {result.stderr}", "error")
                return
            
            _log_and_flush("Installing dependencies with poetry...")
            result = subprocess.run(
                ["poetry", "install"],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                _log_and_flush(f"Failed to install dependencies: {result.stderr}", "error")
                return
            
            _log_and_flush("Restarting application...")
            _log_and_flush("Initiating graceful shutdown...")
            
            RepoRefresher.restart_requested = True
            os.kill(os.getpid(), signal.SIGTERM)
            
        except subprocess.TimeoutExpired:
            _log_and_flush("Update command timed out", "error")
        except Exception as e:
            _log_and_flush(f"Error during update and restart: {e}", "error")
