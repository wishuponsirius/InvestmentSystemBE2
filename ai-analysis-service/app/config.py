import os

class Settings:
    DB_HOST = os.getenv("DB_HOST") or "localhost"
    DB_PORT = os.getenv("DB_PORT") or "5432"
    DB_NAME = os.getenv("DB_NAME") or "investment_db"
    DB_USERNAME = os.getenv("DB_USERNAME") or "postgres"
    DB_PASSWORD = os.getenv("DB_PASSWORD") or "postgres"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyD9TsCJx9vfwQBjPp3ii7InXhlVkF9Hj7I"
    GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite-preview"
    POOL_MIN_SIZE = int(os.getenv("POOL_MIN_SIZE") or 2)
    POOL_MAX_SIZE = int(os.getenv("POOL_MAX_SIZE") or 10)

    @property
    def database_url(self):
        return (
            f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

settings = Settings()
