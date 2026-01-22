"""
GPIO pin configuration for different device types.

Each device type defines:
- available_pins: List of GPIO pins that can be used for sensors
- description: Human-readable device description
"""

DEVICE_GPIO_CONFIG = {
    "raspberry_pi_5": {
        "available_pins": [
            2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
            14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
            24, 25, 26, 27
        ],
        "description": "Raspberry Pi 5 - 26 GPIO pins (BCM numbering)"
    },
    "raspberry_pi_4": {
        "available_pins": [
            2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
            14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
            24, 25, 26, 27
        ],
        "description": "Raspberry Pi 4 - 26 GPIO pins (BCM numbering)"
    },
    # Future device types can be added here:
    # "arduino_uno": { ... },
    # "raspberry_pi_zero": { ... },
}


def get_available_pins(device_type: str) -> list[int]:
    """Get the list of available GPIO pins for the given device type."""
    if device_type not in DEVICE_GPIO_CONFIG:
        raise ValueError(
            f"Unknown device type: {device_type}. "
            f"Available types: {list(DEVICE_GPIO_CONFIG.keys())}"
        )
    return DEVICE_GPIO_CONFIG[device_type]["available_pins"]


def get_device_description(device_type: str) -> str:
    """Get the description for the given device type."""
    if device_type not in DEVICE_GPIO_CONFIG:
        raise ValueError(f"Unknown device type: {device_type}")
    return DEVICE_GPIO_CONFIG[device_type]["description"]
