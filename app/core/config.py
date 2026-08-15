import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    JWT_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_EXPIRE_MINUTES", "60")
    )

    GOOGLE_CLIENT_ID: str = os.getenv(
        "GOOGLE_CLIENT_ID",
        ""
    )


settings = Settings()