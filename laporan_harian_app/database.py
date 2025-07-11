import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

# Konfigurasi Database PostgreSQL
# Gunakan variabel lingkungan DATABASE_URL untuk URL database
# Fallback ke SQLite untuk pengembangan lokal jika variabel lingkungan tidak ada
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/sql_app.db")

# Jika menggunakan PostgreSQL, pastikan URL dimulai dengan 'postgresql'
# SQLAlchemy membutuhkan 'postgresql' bukan 'postgres'
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency untuk mendapatkan sesi database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fungsi untuk membuat semua tabel di database
def create_db_tables():
    Base.metadata.create_all(bind=engine)
