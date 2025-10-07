import os, requests, pdb, logging

from time import sleep
from common.settings import Settings

logger = logging.getLogger(__name__)

class DeviceRegisterer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.settings = Settings()
            cls._instance._register_device()
        return cls._instance

    def _register_device(cls):
        response_status = 000
        while response_status not in [200, 201]:
            try:
                response = requests.post(
                    f"{cls.settings.collector_host}/devices",
                    headers={"X-API-KEY": cls.settings.api_key},
                    json={
                        "id": cls.settings.device_id,
                        "description": cls.settings.description
                    }
                )
                response_status = response.status_code
            except requests.RequestException as e:
                logger.error(f"Could not register device: {e}. Trying again in 10 seconds...")
                response_status = 000
                sleep(10)
                continue
        #pdb.set_trace()
        #os.environ["SENSOR_READER_API_KEY"] = cls.settings.api_key || response
