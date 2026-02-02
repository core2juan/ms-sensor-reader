"""
Base class for analog sensors that use the ADS1115 ADC via I2C.

Extends SensorInterface with ADC initialization and voltage reading capabilities.
"""
import logging

from sensors.sensor_interface import SensorInterface

logger = logging.getLogger(__name__)


class AnalogSensorBase(SensorInterface):
    """
    Base class for sensors that use the ADS1115 ADC.
    
    Initializes I2C communication and provides voltage reading from
    a specified ADC channel (0-3 corresponding to A0-A3).
    """

    def __init__(self, id: str, description: str, channel: int = 0, address: int = 0x48):
        """
        Initialize the analog sensor.
        
        Args:
            id: Unique identifier for the sensor
            description: Human-readable description
            channel: ADC channel (0-3 for A0-A3), default 0
            address: I2C address of the ADS1115, default 0x48
            
        Raises:
            ValueError: If channel is not 0-3
        """
        super().__init__(id, description)
        
        if channel not in (0, 1, 2, 3):
            raise ValueError(f"Invalid channel {channel}. Must be 0-3.")
        
        self._channel = channel
        self._address = address
        
        # Import hardware libraries here to avoid loading on dev machines
        import board
        import busio
        import adafruit_ads1x15.ads1115 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn
        
        # Channel mapping: channel number to ADS1115 pin constant
        channel_map = {
            0: ADS.P0,  # A0
            1: ADS.P1,  # A1
            2: ADS.P2,  # A2
            3: ADS.P3,  # A3
        }
        
        # Initialize I2C and ADC
        self._i2c = busio.I2C(board.SCL, board.SDA)
        self._ads = ADS.ADS1115(self._i2c, address=address)
        self._analog_in = AnalogIn(self._ads, channel_map[channel])
        
        logger.info(f"AnalogSensorBase '{id}' initialized on channel A{channel} (address=0x{address:02x})")

    @property
    def channel(self) -> int:
        """The ADC channel this sensor is using (0-3)."""
        return self._channel

    @property
    def voltage(self) -> float:
        """Read the current voltage from the ADC channel."""
        return self._analog_in.voltage

    @property
    def raw_value(self) -> int:
        """Read the raw ADC value (16-bit)."""
        return self._analog_in.value

    def cleanup(self) -> None:
        """Release I2C resources. Call this when the sensor is no longer needed."""
        if hasattr(self, '_i2c') and self._i2c:
            try:
                self._i2c.deinit()
            except Exception:
                pass  # Ignore errors during cleanup

    def __del__(self):
        """Attempt to cleanup when the sensor is garbage collected."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during garbage collection
