from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='sensor_reader_')

    collector_host: str = "http://localhost:3000"
    token: str = ""
    device_id: str = "test-device-001"
    description: str = "A test device located in test location"
    
    # Repo Refresher settings
    # Dont enable refresher on development. Otherwise your git directory may get corrupted.
    repo_refresher_enabled: bool = False
    repo_check_interval_minutes: int = 30
    repo_branch: str = "main"
    github_app_id: int = 2702768
    github_app_pem_path: str = "repo-refresher.private-key.pem"
    github_repo_owner: str = "core2juan"
    github_repo_name: str = "ms-sensor-reader"