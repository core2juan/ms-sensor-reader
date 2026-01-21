import logging
import sys
import os

from common.device import Device
from common.repo_refresher import RepoRefresher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == "__main__":
    RepoRefresher()
    device = Device()
    exit_code = device.run()
    
    if RepoRefresher.restart_requested:
        logging.info("Restarting with updated code...")
        python = sys.executable
        os.execv(python, [python] + sys.argv)
    
    sys.exit(exit_code)
