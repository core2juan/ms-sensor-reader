import logging, sys, pdb

from time import sleep
from sensors import FloatSensor, EnergyConsumptionSensor
from metrics_exporter import APIExporter, LMDBExporter, LogExporter
from common.device_registerer import DeviceRegisterer
from common.retry_worker import RetryWorker
from common.settings import Settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

settings = Settings()
print(f"current setting {settings.api_key}")
DeviceRegisterer()
settings = Settings()
print(f"current setting {settings.api_key}")

pdb.set_trace()

sensors = []
for time in range(10):
    sensors.append(FloatSensor(f"float_sensor_{time}", f"A test float sensor {time}"))
    sensors.append(EnergyConsumptionSensor(f"energy_sensor_{time}", f"A test energy consumption sensor {time}"))

worker = RetryWorker()

api_exporter = APIExporter()
log_exporter = LogExporter()
lmdb_exporter = LMDBExporter()

while True:
    metrics = [sensor.current_metric() for sensor in sensors]
    log_exporter(metrics)
    if api_exporter(metrics) == 201:
        logging.info(f"Sent metrics to API successfully")
    else:
        lmdb_exporter(metrics)
    sleep(5)
