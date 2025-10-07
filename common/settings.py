from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='sensor_reader_')

    collector_host: str = "http://localhost:3000"
    token: str = ""
    device_id: str = "test-device-001"
    description: str = "A test device located in test location"
