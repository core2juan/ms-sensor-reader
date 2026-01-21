import logging
import signal
import time as time_module
from time import sleep

import psutil

from sensors import FloatSensor, EnergyConsumptionSensor
from metrics_exporter import APIExporter, LMDBExporter, LogExporter
from common.device_registerer import DeviceRegisterer
from common.metric_type import MetricType
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

    def _read_temperature(self) -> float | None:
        # Raspberry Pi: read from thermal zone (returns millidegrees Celsius)
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp_millidegrees = int(f.read().strip())
                return temp_millidegrees / 1000.0
        except (FileNotFoundError, IOError, ValueError):
            pass
        
        # Fallback: try psutil for other platforms
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name in ["coretemp", "cpu_thermal", "cpu-thermal", "k10temp", "acpitz"]:
                    if name in temps:
                        return temps[name][0].current
                first_sensor = list(temps.values())[0]
                if first_sensor:
                    return first_sensor[0].current
        except Exception as e:
            logger.debug(f"Temperature reading not available: {e}")
        return None

    def current_metrics(self) -> dict:
        return {
            "timestamp": int(time_module.time()),
            "metrics": {
                "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
                "memory_usage_percent": psutil.virtual_memory().percent,
                "temperature_celsius": self._read_temperature()
            }
        }

    def run(self):
        logger.info("Starting device...")
        
        DeviceRegisterer().register(shutdown_check=lambda: self._shutdown_requested)
        
        # Initialize sensors
        sensors = []
        for time in range(10):
            sensors.append(FloatSensor(f"float_sensor_{time}", f"A test float sensor {time}"))
            sensors.append(EnergyConsumptionSensor(f"energy_sensor_{time}", f"A test energy consumption sensor {time}"))
        
        # Initialize worker and exporters
        worker = RetryWorker()
        api_exporter = APIExporter()
        log_exporter = LogExporter()
        lmdb_exporter = LMDBExporter()
        
        logger.info("Device running, collecting metrics...")
        
        while not self._shutdown_requested:
            # Collect and export sensor metrics
            sensor_metrics = [sensor.current_metric() for sensor in sensors]
            log_exporter(sensor_metrics)
            sensor_status_code = api_exporter(sensor_metrics, MetricType.SENSOR)
            if sensor_status_code == 201:
                logger.info("Sent sensor metrics to API successfully")
            else:
                lmdb_exporter(sensor_metrics, sensor_status_code, MetricType.SENSOR)
            
            # Collect and export device status metrics
            device_status = self.current_metrics()
            device_status_code = api_exporter(device_status, MetricType.DEVICE_STATUS)
            if device_status_code == 201:
                logger.info("Sent device status to API successfully")
            else:
                lmdb_exporter(device_status, device_status_code, MetricType.DEVICE_STATUS)
            
            sleep(5)
        
        logger.info("Device shutdown complete")
        return 0
