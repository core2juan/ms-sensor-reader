import logging
from .exporter_interface import ExporterInterface

logger = logging.getLogger(__name__)

class LogExporter(ExporterInterface):

    def __call__(self, metrics):
        logger.info(f"Log metrics:{metrics}")
        return True
