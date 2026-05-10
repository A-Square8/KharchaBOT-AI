from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    telegram_bot_token: str
    telegram_webhook_url: str = ""
    
    gemini_api_key: str
    groq_api_key: str = ""
    
    database_url: str
    supabase_url: str = ""
    supabase_key: str = ""
    
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""
    
    chroma_persist_dir: str = "./chroma_data"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
