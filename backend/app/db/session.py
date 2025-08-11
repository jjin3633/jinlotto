import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


def _get_default_sqlite_url() -> str:
    # backend 루트의 data/app.db 사용
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(backend_root, 'data', 'app.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return f"sqlite:///{db_path}"


DATABASE_URL = os.getenv("DATABASE_URL", _get_default_sqlite_url())

# psycopg2-binary 이슈 회피: 드라이버 미지정(postgresql://)이면 psycopg3로 강제
if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL:
    # 예: postgresql:// -> postgresql+psycopg://
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


