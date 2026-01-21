import logging
import signal
import sys
from time import sleep
from sensors import FloatSensor, EnergyConsumptionSensor
from metrics_exporter import APIExporter, LMDBExporter, LogExporter
from common.device_registerer import DeviceRegisterer
from common.retry_worker import RetryWorker

logger = logging.getLogger(__name__)

class Device:
    def __init__(self):
        self._shutdown_requested = False
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._shutdown_requested = True

    def run(self):
        logger.info("Starting device...")
        
        DeviceRegisterer()
        
        sensors = []
        for time in range(10):
            sensors.append(FloatSensor(f"float_sensor_{time}", f"A test float sensor {time}"))
            sensors.append(EnergyConsumptionSensor(f"energy_sensor_{time}", f"A test energy consumption sensor {time}"))
        
        worker = RetryWorker()
        
        api_exporter = APIExporter()
        log_exporter = LogExporter()
        lmdb_exporter = LMDBExporter()
        
        logger.info("Device running, collecting metrics...")
        
        while not self._shutdown_requested:
            metrics = [sensor.current_metric() for sensor in sensors]
            log_exporter(metrics)
            status_code = api_exporter(metrics)
            if status_code == 201:
                logger.info("Sent metrics to API successfully")
            else:
                lmdb_exporter(metrics, status_code)
            sleep(5)
        
        logger.info("Device shutdown complete")
        return 0
