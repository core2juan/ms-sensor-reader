import logging
import json

from common.lmdb_clients import lmdb_write_client
from .exporter_interface import ExporterInterface

class LMDBExporter(ExporterInterface):
    def __call__(cls, metric):
        with lmdb_write_client.begin(write=True) as txn:
            data = json.dumps(metric, separators=(",", ":")).encode("utf-8")
            key = f"{metric['id']}-{metric['timestamp']}".encode()
            txn.put(key, data)
            logging.info(f"Stored metric in LMDB in key: {key}")
        return True
