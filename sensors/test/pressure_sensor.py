"""
Test Pressure Sensor - Simulates pressure readings for development without hardware.

Generates simulated pressure values that oscillate within a configurable range,
useful for testing the monitoring system without actual hardware connected.
"""
import math
import time

from sensors.sensor_interface import SensorInterface


class PressureSensor(SensorInterface):
    """
    Test pressure sensor that generates simulated pressure values.
    
    Simulates realistic pressure fluctuations using a sine wave pattern
    with some randomness to mimic real sensor behavior.
    """

    def __init__(
        self,
        id: str,
        description: str,
        min_pressure: float = 0.0,
        max_pressure: float = 30.0,
        unit: str = "psi",
    ):
        """
        Initialize the test pressure sensor.
        
        Args:
            id: Unique identifier for the sensor
            description: Human-readable description
            min_pressure: Minimum simulated pressure value
            max_pressure: Maximum simulated pressure value
            unit: Pressure unit for display
        """
        super().__init__(id, description)
        self._min_pressure = min_pressure
        self._max_pressure = max_pressure
        self._unit = unit
        self._start_time = time.time()

    def _read_value(self) -> float:
        """
        Generate a simulated pressure reading.
        
        Uses a sine wave pattern to create smooth oscillations
        between min and max pressure values.
        
        Returns:
            Simulated pressure value
        """
        # Create a slow oscillation over ~60 seconds
        elapsed = time.time() - self._start_time
        # Sine wave oscillates between 0 and 1
        normalized = (math.sin(elapsed * 0.1) + 1) / 2
        
        # Map to pressure range
        pressure_range = self._max_pressure - self._min_pressure
        pressure = self._min_pressure + (normalized * pressure_range)
        
        return round(pressure, 2)

    @property
    def unit(self) -> str:
        """The pressure unit (e.g., 'psi', 'bar')."""
        return self._unit

    def current_metric(self):
        """
        Get the current metric with pressure-specific fields.
        
        Returns:
            Dict containing id, description, value, unit, and timestamp
        """
        return {
            "id": self.id,
            "description": self.description,
            "value": self._read_value(),
            "unit": self._unit,
            "timestamp": self._timestamp()
        }
