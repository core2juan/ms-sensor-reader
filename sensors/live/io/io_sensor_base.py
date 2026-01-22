"""
Base class for IO-based sensors that use GPIO pins.

Extends SensorInterface with pin registration and cleanup capabilities.
"""
from sensors.sensor_interface import SensorInterface
from common.pin_registry import PinRegistry


class IOSensorBase(SensorInterface):
    """
    Base class for sensors that use GPIO pins.
    
    Automatically registers the pin with the PinRegistry on initialization
    and provides cleanup method to release the pin.
    """

    def __init__(self, id: str, description: str, pin: int):
        """
        Initialize the IO sensor.
        
        Args:
            id: Unique identifier for the sensor
            description: Human-readable description
            pin: GPIO pin number (BCM numbering)
            
        Raises:
            InvalidPinError: If the pin is not available for the device type
            PinAlreadyInUseError: If the pin is already in use by another sensor
        """
        super().__init__(id, description)
        self._pin = pin
        self._registry = PinRegistry()
        self._registry.register(pin, id)

    @property
    def pin(self) -> int:
        """The GPIO pin number this sensor is using."""
        return self._pin

    def cleanup(self) -> None:
        """Release the GPIO pin. Call this when the sensor is no longer needed."""
        self._registry.release(self._pin)

    def __del__(self):
        """Attempt to cleanup when the sensor is garbage collected."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during garbage collection
