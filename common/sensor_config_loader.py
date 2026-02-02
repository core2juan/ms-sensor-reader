"""
Sensor Configuration Loader

Reads sensor_config.yaml and initializes sensors based on the configuration.
"""
import logging
from pathlib import Path

import yaml

from common.settings import Settings

logger = logging.getLogger(__name__)

# Default config file path (relative to sensor_reader directory)
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "sensor_config.yaml"


def load_sensors_from_config(config_path: str | Path | None = None) -> list:
    settings = Settings()
    
    if not settings.live_sensors_enabled:
        logger.info("Live sensors disabled (set SENSOR_READER_LIVE_SENSORS_ENABLED=true to enable)")
        return []
    
    config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    
    if not config_path.exists():
        logger.warning(f"Sensor config file not found at {config_path}, no live sensors will be loaded")
        return []
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing sensor config file: {e}")
        return []
    
    if not config or 'sensors' not in config:
        logger.info("No sensors defined in config file")
        return []
    
    # Import here to avoid loading gpiozero/adafruit on dev machines
    from sensors.live.io import FloatSensor as LiveFloatSensor
    from sensors.live.analog import PressureSensor as LivePressureSensor
    
    sensors = []
    sensors_config = config['sensors']
    
    # Load IO sensors
    if 'io' in sensors_config:
        io_config = sensors_config['io']
        sensors.extend(_load_io_sensors(io_config, LiveFloatSensor))
    
    # Load analog sensors
    if 'analog' in sensors_config:
        analog_config = sensors_config['analog']
        sensors.extend(_load_analog_sensors(analog_config, LivePressureSensor))
    
    logger.info(f"Loaded {len(sensors)} live sensor(s) from config")
    return sensors


def _load_io_sensors(io_config: dict, FloatSensorClass) -> list:
    """Load IO-based sensors from config."""
    sensors = []
    
    # Load float sensors
    if 'float_sensors' in io_config and io_config['float_sensors']:
        for sensor_def in io_config['float_sensors']:
            try:
                sensor = FloatSensorClass(
                    id=sensor_def['id'],
                    description=sensor_def['description'],
                    pin=sensor_def['pin'],
                    inverted=sensor_def.get('inverted', False)
                )
                sensors.append(sensor)
                logger.info(f"Initialized live FloatSensor '{sensor_def['id']}' on pin {sensor_def['pin']}")
            except KeyError as e:
                logger.error(f"Missing required field {e} in float sensor config: {sensor_def}")
            except Exception as e:
                logger.error(f"Failed to initialize float sensor: {e}")
    
    return sensors


def _load_analog_sensors(analog_config: dict, PressureSensorClass) -> list:
    """Load analog sensors from config."""
    sensors = []
    
    # Load pressure sensors
    if 'pressure_sensors' in analog_config and analog_config['pressure_sensors']:
        for sensor_def in analog_config['pressure_sensors']:
            try:
                sensor = PressureSensorClass(
                    id=sensor_def['id'],
                    description=sensor_def['description'],
                    channel=sensor_def.get('channel', 0),
                    min_pressure=sensor_def.get('min_pressure', 0.0),
                    max_pressure=sensor_def.get('max_pressure', 30.0),
                    unit=sensor_def.get('unit', 'psi'),
                )
                sensors.append(sensor)
                logger.info(
                    f"Initialized live PressureSensor '{sensor_def['id']}' on channel A{sensor_def.get('channel', 0)}"
                )
            except KeyError as e:
                logger.error(f"Missing required field {e} in pressure sensor config: {sensor_def}")
            except Exception as e:
                logger.error(f"Failed to initialize pressure sensor: {e}")
    
    return sensors
