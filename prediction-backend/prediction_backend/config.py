import os
from typing import Optional


def get_database_url() -> str:
    """Return the database URL from env, preferring MARKET_DATABASE_URL, then NHL_DATABASE_URL, then DATABASE_URL.

    Raises if neither is set.
    """
    db_url: Optional[str] = (
        os.environ.get("MARKET_DATABASE_URL")
        or os.environ.get("NHL_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL or NHL_DATABASE_URL must be set to start the prediction backend."
        )
    return db_url


PORT: int = int(os.environ.get("PORT", "8100"))
HOST: str = os.environ.get("HOST", "0.0.0.0")
API_PREFIX: str = "/api"


