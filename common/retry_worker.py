import json
import logging
import threading

from time import sleep

from common.lmdb_clients import lmdb_write_client, lmdb_read_client
from common.metric_type import MetricType
from metrics_exporter import APIExporter


class RetryWorker:

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._api_exporter = APIExporter()
        self._stop = threading.Event()
        self._retry_thread = threading.Thread(target=self._retry_loop, daemon=True)
        self._retry_thread.start()

    def _get_lmdb_keys(self):
        with lmdb_read_client.begin() as txn:
            with txn.cursor() as cursor:
                keys = [key.decode() for key, _ in cursor]
        logging.info(f"LMDB keys: {keys}")
        return keys

    def _get_stored_batch(self, key: str):
        with lmdb_read_client.begin() as txn:
            data = txn.get(key.encode())
            if data:
                return json.loads(data.decode())
        return None

    def _delete_stored_batch(self, key: str):
        with lmdb_write_client.begin(write=True) as txn:
            if txn.delete(key.encode()):
                logging.info(f"Deleted batch from LMDB with key: {key}")
                return True
            logging.warning(f"Failed to delete batch from LMDB with key: {key}")
            return False

    def _parse_metric_type_from_key(self, key: str) -> MetricType:
        """Parse the metric type from the LMDB key prefix."""
        if key.startswith(MetricType.DEVICE_STATUS.value):
            return MetricType.DEVICE_STATUS
        elif key.startswith(MetricType.SENSOR.value):
            return MetricType.SENSOR
        # Legacy support for old 'batch-' keys (treat as sensor metrics)
        return MetricType.SENSOR

    def _retry_batch(self, key: str):
        batch = self._get_stored_batch(key)
        if not batch:
            logging.info(f"No batch found for key: {key}")
            return False

        # Get payload and metric type from stored data
        # Support both old 'metrics' key and new 'payload' key for backwards compatibility
        payload = batch.get("payload") or batch.get("metrics")
        status_code = batch.get("status_code")
        
        # Determine metric type from stored data or key prefix
        stored_type = batch.get("metric_type")
        if stored_type:
            metric_type = MetricType(stored_type)
        else:
            metric_type = self._parse_metric_type_from_key(key)

        if status_code == 422:
            logging.warning(f"Batch {key} has validation error (422), skipping retry")
            self._delete_stored_batch(key)
            return False

        for attempt in range(1, self.max_retries + 1):
            response = self._api_exporter(payload, metric_type)
            if response == 201:
                logging.info(f"Successfully sent {metric_type.value} batch for key: {key} on attempt {attempt}")
                self._delete_stored_batch(key)
                return True
            logging.error(f"Attempt {attempt} failed for key: {key}, status code: {response}")
            sleep(1)
        return False

    def _retry_loop(self):
        logging.info("Starting RetryWorker thread")
        while not self._stop.is_set():
            keys = self._get_lmdb_keys()
            for key in keys:
                self._retry_batch(key)
            logging.info("Retry cycle complete, sleeping for 10 seconds")
            self._stop.wait(10)
