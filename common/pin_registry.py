"""
Pin Registry - Singleton for tracking GPIO pin usage.

Prevents multiple sensors from using the same pin and validates
that pins are available for the configured device type.
"""
import logging

from common.settings import Settings
from common.gpio_config import get_available_pins

logger = logging.getLogger(__name__)


class PinAlreadyInUseError(Exception):
    """Raised when attempting to register a pin that's already in use."""
    pass


class InvalidPinError(Exception):
    """Raised when attempting to use a pin that's not available for the device type."""
    pass


class PinRegistry:
    """Singleton registry for tracking GPIO pin usage across sensors."""
    
    _instance = None
    _pins_in_use: dict[int, str] = {}  # pin -> sensor_id

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._pins_in_use = {}
            settings = Settings()
            cls._device_type = settings.device_type
            cls._available_pins = get_available_pins(settings.device_type)
            logger.info(
                f"PinRegistry initialized for {cls._device_type} "
                f"with {len(cls._available_pins)} available pins"
            )
        return cls._instance

    def register(self, pin: int, sensor_id: str) -> None:
        """
        Register a pin for use by a sensor.
        
        Args:
            pin: The GPIO pin number (BCM numbering)
            sensor_id: The ID of the sensor using this pin
            
        Raises:
            InvalidPinError: If the pin is not available for the device type
            PinAlreadyInUseError: If the pin is already registered to another sensor
        """
        if pin not in self._available_pins:
            raise InvalidPinError(
                f"Pin {pin} is not available for {self._device_type}. "
                f"Available pins: {self._available_pins}"
            )
        
        if pin in self._pins_in_use:
            existing_sensor = self._pins_in_use[pin]
            raise PinAlreadyInUseError(
                f"Pin {pin} is already in use by sensor '{existing_sensor}'. "
                f"Cannot register for sensor '{sensor_id}'."
            )
        
        self._pins_in_use[pin] = sensor_id
        logger.info(f"Pin {pin} registered for sensor '{sensor_id}'")

    def release(self, pin: int) -> None:
        """
        Release a pin, making it available for other sensors.
        
        Args:
            pin: The GPIO pin number to release
        """
        if pin in self._pins_in_use:
            sensor_id = self._pins_in_use.pop(pin)
            logger.info(f"Pin {pin} released from sensor '{sensor_id}'")
        else:
            logger.warning(f"Attempted to release pin {pin} that was not registered")

    def is_pin_available(self, pin: int) -> bool:
        """Check if a pin is available for use."""
        return pin in self._available_pins and pin not in self._pins_in_use

    def get_sensor_for_pin(self, pin: int) -> str | None:
        """Get the sensor ID using a specific pin, or None if not in use."""
        return self._pins_in_use.get(pin)

    def get_used_pins(self) -> dict[int, str]:
        """Get a copy of all pins currently in use."""
        return self._pins_in_use.copy()
