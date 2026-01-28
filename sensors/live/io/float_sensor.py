"""
Live Float Sensor - Reads ON/OFF state from a GPIO pin.

Float sensors are typically connected:
- One wire to ground
- One wire to a GPIO pin (with internal pull-up resistor enabled)

Supports both Normally Open (NO) and Normally Closed (NC) float sensors
via the `inverted` parameter.
"""
import logging

from gpiozero import Button

from .io_sensor_base import IOSensorBase

logger = logging.getLogger(__name__)


class FloatSensor(IOSensorBase):
    """
    Float sensor that reads ON/OFF state from a GPIO pin.
    
    Uses gpiozero's Button class with pull-up resistor enabled.
    
    For Normally Open (NO) sensors: inverted=False (default)
      - Float UP (floating) → switch closes → returns 1.0
      - Float DOWN → switch open → returns 0.0
    
    For Normally Closed (NC) sensors: inverted=True
      - Float UP (floating) → switch opens → returns 1.0
      - Float DOWN → switch closes → returns 0.0
    """

    def __init__(self, id: str, description: str, pin: int, inverted: bool = False):
        """
        Initialize the float sensor.
        
        Args:
            id: Unique identifier for the sensor
            description: Human-readable description
            pin: GPIO pin number (BCM numbering)
            inverted: Set True for Normally Closed (NC) sensors
        """
        super().__init__(id, description, pin)
        self._inverted = inverted
        # Use Button with pull_up=True: pin is HIGH when open, LOW when grounded
        self._button = Button(pin, pull_up=True)
        logger.info(f"FloatSensor '{id}' initialized on pin {pin} (inverted={inverted})")

    def _read_value(self) -> float:
        """
        Read the current state of the float sensor.
        
        Returns:
            1.0 if float is UP (floating/triggered)
            0.0 if float is DOWN (not floating)
        """
        pressed = self._button.is_pressed
        if self._inverted:
            pressed = not pressed
        return 1.0 if pressed else 0.0

    def cleanup(self) -> None:
        """Release the GPIO pin and close the button device."""
        if hasattr(self, '_button') and self._button:
            self._button.close()
        super().cleanup()
