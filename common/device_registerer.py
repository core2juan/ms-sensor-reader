import os, requests, logging

from time import sleep
from common.settings import Settings

logger = logging.getLogger(__name__)


class DeviceRegisterer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.settings = Settings()
            cls._shutdown_check = None
        return cls._instance

    def register(self, shutdown_check=None):
        """
        Register the device with the collector API.
        
        Args:
            shutdown_check: Optional callable that returns True if shutdown was requested.
        """
        self._shutdown_check = shutdown_check or (lambda: False)
        
        response_status = 000
        while response_status not in [200, 201] and not self._shutdown_check():
            try:
                self.settings = Settings()
                headers = {}
                if self.settings.token:
                    headers["X-API-KEY"] = self.settings.token
                    
                response = requests.post(
                    f"{self.settings.collector_host}/devices",
                    headers=headers,
                    json={
                        "id": self.settings.device_id,
                        "description": self.settings.description
                    },
                    timeout=5
                )
                response_status = response.status_code
                if response_status in [200, 201]:
                    data = response.json()
                    token = data.get("token")
                    if token:
                        os.environ["SENSOR_READER_TOKEN"] = token
                        logger.info("Device registered successfully with token")
                    else:
                        logger.error("No token received from server")
                        response_status = 000
            except requests.RequestException as e:
                logger.error(f"Could not register device: {e}. Trying again in 10 seconds...")
                response_status = 000
                for _ in range(10):
                    if self._shutdown_check():
                        logger.info("Registration stopped due to shutdown signal")
                        return
                    sleep(1)
                continue
        
        if self._shutdown_check():
            logger.info("Registration incomplete due to shutdown")
