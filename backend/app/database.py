from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from app.config import DATABASE_URL, USES_NEON_POOLER

_engine_kwargs: dict = {"pool_pre_ping": True, "pool_recycle": 300}
if USES_NEON_POOLER:
    # Neon pooled endpoint uses PgBouncer. Disable SQLAlchemy's own pool.
    _engine_kwargs["poolclass"] = NullPool

engine = create_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()