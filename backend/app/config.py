import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv

load_dotenv()


def normalize_database_url(raw_url: str) -> str:
    """Accept Neon / Render postgres URLs and make them SQLAlchemy-safe.

    - postgres://  → postgresql://  (SQLAlchemy 2 requires the latter)
    - Neon requires TLS; add sslmode=require when the host is neon.tech
    """
    url = (raw_url or "").strip().strip('"').strip("'")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    query = dict(parse_qsl(parts.query, keep_blank_values=True))

    if "neon.tech" in host and "sslmode" not in {k.lower() for k in query}:
        query["sslmode"] = "require"

    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Create a local .env file before running the app.")

DATABASE_URL = normalize_database_url(DATABASE_URL)
USES_NEON_POOLER = "-pooler" in DATABASE_URL or "pgbouncer=true" in DATABASE_URL.lower()

# OpenRouteService – read from .env; warn at startup if absent (not fatal so the
# rest of the app can still run, but /route endpoints will fail at call-time).
ORS_API_KEY: str | None = os.getenv("ORS_API_KEY")

# Nominatim requires a descriptive User-Agent string per their usage policy.
NOMINATIM_USER_AGENT: str = os.getenv("NOMINATIM_USER_AGENT", "FleetFlow/1.0 (fleet-logistics-app)")