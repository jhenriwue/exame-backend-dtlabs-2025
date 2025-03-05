import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dtlabs.database import Base, get_db
from fastapi.testclient import TestClient
from dtlabs.app import app

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)  
    session = TestingSessionLocal()
    yield session  
    session.close()
    Base.metadata.drop_all(bind=engine) 

@pytest.fixture(scope="module")
def client():
    return TestClient(app)
