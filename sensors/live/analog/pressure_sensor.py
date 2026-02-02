"""
Live Pressure Sensor - Reads pressure from an analog sensor via ADS1115 ADC.

Pressure sensors typically output a voltage proportional to pressure:
- 0.5V at minimum pressure (e.g., 0 PSI)
- 4.5V at maximum pressure (e.g., 30 PSI)

When using a voltage divider to protect the ADC from voltages > 3.3V,
the divider ratio must be accounted for in the conversion.

Example voltage divider (10kΩ / 33kΩ):
- Ratio = 33kΩ / (10kΩ + 33kΩ) ≈ 0.7674
- 4.5V sensor output → ~3.45V at ADC (safe for 3.3V ADC reference)
- 0.5V sensor output → ~0.38V at ADC
"""
import logging

from .analog_sensor_base import AnalogSensorBase

logger = logging.getLogger(__name__)

# Default voltage divider ratio for 10kΩ / 33kΩ divider
DEFAULT_VOLTAGE_DIVIDER_RATIO = 33.0 / (10.0 + 33.0)  # ≈ 0.7674

# Default sensor voltage range (standard 0.5V - 4.5V output)
DEFAULT_MIN_VOLTAGE = 0.5
DEFAULT_MAX_VOLTAGE = 4.5


class PressureSensor(AnalogSensorBase):
    """
    Pressure sensor that reads analog voltage and converts to pressure units.
    
    Uses linear interpolation to convert the sensor's voltage output
    to pressure values. Accounts for voltage divider if present.
    """

    def __init__(
        self,
        id: str,
        description: str,
        channel: int = 0,
        min_pressure: float = 0.0,
        max_pressure: float = 30.0,
        unit: str = "psi",
        voltage_divider_ratio: float = DEFAULT_VOLTAGE_DIVIDER_RATIO,
        min_voltage: float = DEFAULT_MIN_VOLTAGE,
        max_voltage: float = DEFAULT_MAX_VOLTAGE,
        address: int = 0x48,
    ):
        """
        Initialize the pressure sensor.
        
        Args:
            id: Unique identifier for the sensor
            description: Human-readable description
            channel: ADC channel (0-3 for A0-A3), default 0
            min_pressure: Minimum pressure reading (at min_voltage), default 0.0
            max_pressure: Maximum pressure reading (at max_voltage), default 30.0
            unit: Pressure unit for display (e.g., "psi", "bar"), default "psi"
            voltage_divider_ratio: Ratio of voltage divider (V_out / V_in), default ~0.767
            min_voltage: Sensor output voltage at minimum pressure, default 0.5V
            max_voltage: Sensor output voltage at maximum pressure, default 4.5V
            address: I2C address of the ADS1115, default 0x48
        """
        super().__init__(id, description, channel, address)
        
        self._min_pressure = min_pressure
        self._max_pressure = max_pressure
        self._unit = unit
        self._voltage_divider_ratio = voltage_divider_ratio
        self._min_voltage = min_voltage
        self._max_voltage = max_voltage
        
        # Pre-calculate the voltage range for efficiency
        self._voltage_range = max_voltage - min_voltage
        self._pressure_range = max_pressure - min_pressure
        
        logger.info(
            f"PressureSensor '{id}' initialized: "
            f"channel=A{channel}, range={min_pressure}-{max_pressure} {unit}, "
            f"voltage_divider_ratio={voltage_divider_ratio:.4f}"
        )

    def _get_original_voltage(self) -> float:
        """
        Get the original sensor voltage before the voltage divider.
        
        Returns:
            The calculated original sensor voltage
        """
        adc_voltage = self.voltage
        return adc_voltage / self._voltage_divider_ratio

    def _voltage_to_pressure(self, voltage: float) -> float:
        """
        Convert sensor voltage to pressure.
        
        Args:
            voltage: The original sensor voltage (before voltage divider)
            
        Returns:
            The calculated pressure value
        """
        # Clamp voltage to valid range
        voltage = max(self._min_voltage, min(self._max_voltage, voltage))
        
        # Linear interpolation
        normalized = (voltage - self._min_voltage) / self._voltage_range
        pressure = self._min_pressure + (normalized * self._pressure_range)
        
        return round(pressure, 2)

    def _read_value(self) -> float:
        """
        Read the current pressure from the sensor.
        
        Returns:
            The pressure value in the configured unit
        """
        original_voltage = self._get_original_voltage()
        return self._voltage_to_pressure(original_voltage)

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
