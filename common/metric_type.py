from enum import Enum


class MetricType(Enum):
    """Enum to distinguish between different metric types for routing and storage."""
    SENSOR = "sensor-batch"
    DEVICE_STATUS = "device-status"
