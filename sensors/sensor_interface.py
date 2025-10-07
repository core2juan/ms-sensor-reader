import time

class SensorInterface:

    def __init__(self, id: str, description: str):
        self.id = id
        self.description = f"{self.__class__.__name__}: {description}"

    def _timestamp(self):
        return int(time.time())

    def _read_value(self):
        raise NotImplementedError("_read_value must be implemented by subclasses")

    def current_metric(self):
        return {
            "id": self.id,
            "description": self.description,
            "value": self._read_value(),
            "timestamp": self._timestamp()
        }
