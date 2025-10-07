from sensors.sensor_interface import SensorInterface

class FloatSensor(SensorInterface):

    def _read_value(self):
        self._internal_counter = 0 if not hasattr(self, '_internal_counter') else self._internal_counter
        value = 1.0 if self._internal_counter % 5 == 0 else 0.0
        self._internal_counter += 1
        self._internal_counter = 0 if self._internal_counter == 1000 else self._internal_counter
        return value
