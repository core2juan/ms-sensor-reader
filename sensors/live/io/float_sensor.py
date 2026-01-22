"""
Live Float Sensor - Reads ON/OFF state from a GPIO pin.

Float sensors are typically connected:
- One wire to ground
- One wire to a GPIO pin (with internal pull-up resistor enabled)

When the float is triggered (e.g., water level rises), the circuit closes
and the pin reads LOW (grounded), which we interpret as ON (1.0).
"""
import logging

from gpiozero import Button

from .io_sensor_base import IOSensorBase

logger = logging.getLogger(__name__)


class FloatSensor(IOSensorBase):
    """
    Float sensor that reads ON/OFF state from a GPIO pin.
    
    Uses gpiozero's Button class with pull-up resistor enabled.
    When the float switch closes (grounds the pin), is_pressed = True = ON.
    """

    def __init__(self, id: str, description: str, pin: int):
        """
        Initialize the float sensor.
        
        Args:
            id: Unique identifier for the sensor
            description: Human-readable description
            pin: GPIO pin number (BCM numbering)
        """
        super().__init__(id, description, pin)
        # Use Button with pull_up=True: pin is HIGH when open, LOW when grounded
        self._button = Button(pin, pull_up=True)
        logger.info(f"FloatSensor '{id}' initialized on pin {pin}")

    def _read_value(self) -> float:
        """
        Read the current state of the float sensor.
        
        Returns:
            1.0 if the float switch is closed (triggered/ON)
            0.0 if the float switch is open (not triggered/OFF)
        """
        return 1.0 if self._button.is_pressed else 0.0

    def cleanup(self) -> None:
        """Release the GPIO pin and close the button device."""
        if hasattr(self, '_button') and self._button:
            self._button.close()
        super().cleanup()
