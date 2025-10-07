import logging
import requests
from .exporter_interface import ExporterInterface

logger = logging.getLogger(__name__)

class APIExporter(ExporterInterface):
    COLLECTOR_HOST = "http://localhost:3000"
    API_KEY = "c4bbe042e487196608078fd42d1d29d683190faae185e1c5d7df99fc4c2e29ca3a3c6b6ab65c88cdeca3f23501bb63ce7fb881d34b413764733c7c2d25dad5e6"
    DEVICE_ID = "test-device-001"

    def __call__(cls, metrics):
        try:
            response = requests.post(f"{cls.COLLECTOR_HOST}/metrics", json=metrics)
            return response.status_code
        except requests.RequestException as e:
            logger.error(f"Error sending metric to API: {e}")
            return 500
