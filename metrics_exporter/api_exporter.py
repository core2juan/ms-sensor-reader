import logging
import requests
from .exporter_interface import ExporterInterface
from common.settings import Settings
from common.device_registerer import DeviceRegisterer

logger = logging.getLogger(__name__)

class APIExporter(ExporterInterface):
    def __init__(self):
        self.settings = Settings()
        self.device_registerer = DeviceRegisterer()

    def __call__(cls, metrics):
        try:
            cls.settings = Settings()
            response = requests.post(
                f"{cls.settings.collector_host}/metrics",
                headers={"X-API-KEY": cls.settings.token},
                json=metrics
            )
            
            if response.status_code == 401:
                logger.warning("Token expired or invalid, re-registering device...")
                cls.device_registerer.register()
                cls.settings = Settings()
                response = requests.post(
                    f"{cls.settings.collector_host}/metrics",
                    headers={"X-API-KEY": cls.settings.token},
                    json=metrics
                )
            
            if response.status_code != 201:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", "Unknown error")
                    logger.error(f"API returned status {response.status_code}: {error_msg}")
                except:
                    logger.error(f"API returned status {response.status_code}: {response.text}")
            
            return response.status_code
        except requests.RequestException as e:
            logger.error(f"Error sending metric to API: {e}")
            return 500
