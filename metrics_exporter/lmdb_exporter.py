import logging
import json
import time

from common.lmdb_clients import lmdb_write_client
from .exporter_interface import ExporterInterface

class LMDBExporter(ExporterInterface):
    def __call__(cls, metrics, status_code=None):
        with lmdb_write_client.begin(write=True) as txn:
            batch_data = {
                "metrics": metrics,
                "status_code": status_code
            }
            data = json.dumps(batch_data, separators=(",", ":")).encode("utf-8")
            key = f"batch-{int(time.time())}".encode()
            txn.put(key, data)
            logging.info(f"Stored {len(metrics)} metrics in LMDB with key: {key}, status: {status_code}")
        return True
