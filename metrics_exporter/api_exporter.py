import logging
import requests
from .exporter_interface import ExporterInterface
from common.settings import Settings
from common.device_registerer import DeviceRegisterer
from common.metric_type import MetricType

logger = logging.getLogger(__name__)

# Endpoint mapping for each metric type
METRIC_TYPE_ENDPOINTS = {
    MetricType.SENSOR: "/metrics",
    MetricType.DEVICE_STATUS: "/devices/status",
}


class APIExporter(ExporterInterface):
    def __init__(self):
        self.settings = Settings()
        self.device_registerer = DeviceRegisterer()

    def _get_endpoint(self, metric_type: MetricType) -> str:
        """Get the API endpoint for the given metric type."""
        return METRIC_TYPE_ENDPOINTS[metric_type]

    def _send_request(self, endpoint: str, payload):
        """Send a POST request to the specified endpoint."""
        return requests.post(
            f"{self.settings.collector_host}{endpoint}",
            headers={"X-API-KEY": self.settings.token},
            json=payload
        )

    def __call__(self, payload, metric_type: MetricType = MetricType.SENSOR):
        try:
            self.settings = Settings()
            endpoint = self._get_endpoint(metric_type)
            response = self._send_request(endpoint, payload)
            
            if response.status_code == 401:
                logger.warning("Token expired or invalid, re-registering device...")
                self.device_registerer.register()
                self.settings = Settings()
                response = self._send_request(endpoint, payload)
            
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
