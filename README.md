# Sensor Reader

A Python-based monitoring client that collects sensor metrics and transmits them to a central monitoring API. Designed for deployment on Raspberry Pi devices with automatic code updates via GitHub App integration.

## Features

- **Device Registration**: Automatic device registration with token-based authentication
- **Token Management**: Automatic token refresh when expired
- **Multiple Sensor Types**: Support for Float and Energy Consumption sensors (extensible)
- **Reliable Metric Delivery**: 
  - Primary delivery via HTTP API
  - Offline resilience with LMDB local storage
  - Automatic retry mechanism for failed transmissions
- **Auto-Update**: Automatic code updates from GitHub using GitHub App authentication
- **Graceful Shutdown**: Proper signal handling for clean process termination
- **Production-Ready**: Optimized for resource-constrained devices like Raspberry Pi

## Architecture

### Core Components

- **Device**: Main controller managing the execution lifecycle
- **DeviceRegisterer**: Handles device registration and token management
- **Sensors**: Pluggable sensor implementations (FloatSensor, EnergyConsumptionSensor)
- **Exporters**: Multiple export strategies (API, LMDB, Logs)
- **RetryWorker**: Background worker for retrying failed metric transmissions
- **RepoRefresher**: Automatic code update manager using GitHub App

### Data Flow

```
Sensors → Collect Metrics → API Exporter
                                ↓ (if fails)
                           LMDB Storage
                                ↓
                          RetryWorker → API Exporter
```

## Installation

### Prerequisites

- Python 3.13.3
- Poetry (Python dependency management)
- Git (for auto-updates)

### Setup

```bash
# Clone the repository (on development machine)
git clone https://github.com/core2juan/ms-sensor-reader.git
cd sensor_reader

# Install dependencies
poetry install

# Create environment configuration
cp .env.example .env
# Edit .env with your settings
```

## Configuration

Configuration is managed via environment variables with the prefix `SENSOR_READER_`. You can set them in a `.env` file or as system environment variables.

### Required Settings

```bash
SENSOR_READER_DEVICE_ID=raspberry-pi-001
SENSOR_READER_DESCRIPTION=Raspberry Pi in living room
SENSOR_READER_COLLECTOR_HOST=http://your-api-server:3000
SENSOR_READER_TOKEN=  # Auto-populated after first registration
```

### Repo Refresher Settings (Optional)

```bash
SENSOR_READER_REPO_REFRESHER_ENABLED=True
SENSOR_READER_REPO_CHECK_INTERVAL_MINUTES=30
SENSOR_READER_REPO_BRANCH=main
SENSOR_READER_GITHUB_APP_ID=123456
SENSOR_READER_GITHUB_APP_PEM_PATH=repo-refresher.private-key.pem
SENSOR_READER_GITHUB_REPO_OWNER=core2juan
SENSOR_READER_GITHUB_REPO_NAME=ms-sensor-reader
```

## Usage

### Development

```bash
# Run the sensor reader
poetry run python main.py

# The device will:
# 1. Register with the API (or refresh token if needed)
# 2. Start collecting metrics from configured sensors
# 3. Send metrics every 5 seconds
# 4. Store failed metrics in LMDB for retry
```

### Production (as a systemd service)

```bash
# Create service file
sudo nano /etc/systemd/system/sensor-reader.service
```

```ini
[Unit]
Description=Sensor Reader Monitoring Client
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/sensor_reader
Environment="SENSOR_READER_DEVICE_ID=raspberry-pi-001"
Environment="SENSOR_READER_COLLECTOR_HOST=http://api-server:3000"
Environment="SENSOR_READER_REPO_REFRESHER_ENABLED=True"
ExecStart=/home/pi/.local/bin/poetry run python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable sensor-reader
sudo systemctl start sensor-reader

# Check status
sudo systemctl status sensor-reader

# View logs
sudo journalctl -u sensor-reader -f
```

## Deployment to Raspberry Pi

### Initial Deployment

```bash
# From your development machine
cd /path/to/monitoring_system

# Copy the entire project (including .git for auto-updates)
rsync -av --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='data.lmdb' \
          --exclude='.env' \
          sensor_reader/ pi@raspberry-pi:/home/pi/sensor_reader/

# Copy GitHub App PEM file (for auto-updates)
scp sensor_reader/repo-refresher.private-key.pem pi@raspberry-pi:/home/pi/sensor_reader/

# Install lgpio on the python target
sudo apt install python3-dev build-essential swig liblgpio-dev
poetry run pip install lgpio
```

### On the Raspberry Pi

```bash
cd /home/pi/sensor_reader

# Install dependencies
poetry install

# Create environment configuration
cat > .env << EOF
SENSOR_READER_DEVICE_ID=raspberry-pi-001
SENSOR_READER_DESCRIPTION=Raspberry Pi in production
SENSOR_READER_COLLECTOR_HOST=http://your-api-server:3000
SENSOR_READER_REPO_REFRESHER_ENABLED=True
SENSOR_READER_GITHUB_APP_ID=your_app_id
SENSOR_READER_GITHUB_APP_PEM_PATH=repo-refresher.private-key.pem
SENSOR_READER_GITHUB_REPO_OWNER=core2juan
SENSOR_READER_GITHUB_REPO_NAME=ms-sensor-reader
SENSOR_READER_REPO_BRANCH=main
EOF

# Test run
poetry run python main.py
```

### Auto-Update Mechanism

Once deployed with RepoRefresher enabled, the device will:

1. Check for updates every 30 minutes (configurable)
2. Fetch only the latest commit (shallow fetch to minimize storage)
3. Pull changes if updates are available
4. Run `poetry install` to update dependencies
5. Clean up git history with `git gc`
6. Gracefully restart the application

**Security Note**: The GitHub App PEM file provides secure, limited-scope access to your repository without exposing personal credentials on the device.

## Development

### Adding New Sensors

1. Create a new sensor class in `sensors/` directory
2. Inherit from `SensorInterface`
3. Implement `current_metric()` method
4. Register in `sensors/__init__.py`

Example:

```python
from .sensor_interface import SensorInterface

class TemperatureSensor(SensorInterface):
    def __init__(self, external_id: str, description: str):
        super().__init__(external_id, f"TemperatureSensor: {description}")
    
    def current_metric(self) -> dict:
        # Read temperature from hardware
        temperature = read_temperature()
        return {
            "id": self.external_id,
            "description": self.description,
            "value": temperature,
            "timestamp": int(time.time())
        }
```

### Adding New Exporters

1. Create a new exporter class in `metrics_exporter/` directory
2. Inherit from `ExporterInterface`
3. Implement `__call__()` method
4. Register in `metrics_exporter/__init__.py`

## Troubleshooting

### Device Registration Fails

```bash
# Check API server is accessible
curl http://your-api-server:3000/devices

# Check logs for error details
tail -f /var/log/sensor-reader.log
```

### Metrics Not Being Sent

- Check LMDB storage: Failed metrics are stored in `data.lmdb/`
- RetryWorker will automatically retry every 10 seconds
- Check API authentication token is valid

### Auto-Update Not Working

```bash
# Verify GitHub App credentials
echo $SENSOR_READER_GITHUB_APP_ID
ls -la repo-refresher.private-key.pem

# Check git remote configuration
git remote -v

# Manual update test
poetry run python -c "from common.repo_refresher import RepoRefresher; r = RepoRefresher(); r._check_and_update()"
```

### Graceful Shutdown Hanging

If Ctrl+C doesn't work:
- First press: Initiates graceful shutdown
- Device will exit within 1 second during retry loops
- If stuck, check that signal handlers are properly registered

## Project Structure

```
sensor_reader/
├── common/
│   ├── device.py              # Main device controller
│   ├── device_registerer.py   # Device registration & token management
│   ├── repo_refresher.py      # Auto-update mechanism
│   ├── retry_worker.py        # Failed metrics retry worker
│   ├── settings.py            # Configuration management
│   └── lmdb_clients.py        # LMDB database clients
├── sensors/
│   ├── sensor_interface.py    # Base sensor interface
│   ├── float_sensor.py        # Float sensor implementation
│   └── energy_consumption_sensor.py
├── metrics_exporter/
│   ├── exporter_interface.py  # Base exporter interface
│   ├── api_exporter.py        # HTTP API exporter
│   ├── lmdb_exporter.py       # Local storage exporter
│   └── log_exporter.py        # Logging exporter
├── main.py                    # Application entry point
├── pyproject.toml             # Python dependencies
└── README.md                  # This file
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
