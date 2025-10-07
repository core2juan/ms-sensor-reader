import threading
from time import sleep

from sensors.sensor_interface import SensorInterface

class EnergyConsumptionSensor(SensorInterface):

    def __init__(self, id: str, description: str):
        super().__init__(id, description)
        self._value = 0.0
        self._stop = threading.Event()
        self._update_thread = threading.Thread(target=self._update_value, daemon=True)
        self._update_thread.start()

    def _read_value(self):
        return self._value

    def _update_value(self):
        internal_counter = 0
        while not self._stop.is_set():
            value = 0.0 if internal_counter % 5 == 0 else 100.0
            internal_counter += 1
            internal_counter = 0 if internal_counter == 1000 else internal_counter
            self._value = value
            #print(f"EnergyConsumptionSensor {self.id} updated value to {self._value}")
            sleep(0.2)

    def current_metric(self):
        return {
            "id": self.id,
            "description": self.description,
            "value": self._read_value(),
            "timestamp": self._timestamp()
        }
