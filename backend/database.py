from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager

sqlite_file_name = "byte.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}

# Increased pool size to handle concurrent WebSocket connections
engine = create_engine(
    sqlite_url, 
    connect_args=connect_args,
    pool_size=20,          # Base pool size
    max_overflow=30,       # Allow up to 50 total connections (20 + 30)
    pool_pre_ping=True,    # Verify connections before use
    pool_recycle=3600,     # Recycle connections after 1 hour
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    """FastAPI dependency for HTTP endpoints - yields session with auto-cleanup"""
    with Session(engine) as session:
        yield session

@contextmanager
def get_db_session():
    """Context manager for manual session management (WebSockets, background tasks)"""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
