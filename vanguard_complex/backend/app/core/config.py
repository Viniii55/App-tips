from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    PROJECT_NAME: str = "Vanguard Core"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days
    
    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # Compliance
    COMPLIANCE_MODE: bool = True
    LEGAL_ENTITY_CNPJ: str = "00.000.000/0001-00"  # Placeholder

    model_config = {
        "case_sensitive": True,
        "env_file": ".env"
    }

settings = Settings()
