import logging
import json
import time

from common.lmdb_clients import lmdb_write_client
from common.metric_type import MetricType
from .exporter_interface import ExporterInterface


class LMDBExporter(ExporterInterface):
    def __call__(self, payload, status_code=None, metric_type: MetricType = MetricType.SENSOR):
        with lmdb_write_client.begin(write=True) as txn:
            batch_data = {
                "payload": payload,
                "status_code": status_code,
                "metric_type": metric_type.value
            }
            data = json.dumps(batch_data, separators=(",", ":")).encode("utf-8")
            # Use metric_type.value as key prefix for clear segregation
            key = f"{metric_type.value}-{int(time.time())}".encode()
            txn.put(key, data)
            
            # Log appropriate message based on metric type
            if metric_type == MetricType.SENSOR:
                logging.info(f"Stored {len(payload)} sensor metrics in LMDB with key: {key}, status: {status_code}")
            else:
                logging.info(f"Stored device status in LMDB with key: {key}, status: {status_code}")
        return True
