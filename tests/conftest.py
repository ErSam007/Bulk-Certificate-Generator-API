import tempfile
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
import app.service as service_module

@pytest.fixture(scope="session")
def temp_storage():
    temp_dir = Path(tempfile.mkdtemp(prefix="test_cert_storage_"))
    original_storage = service_module.STORAGE_DIR
    service_module.STORAGE_DIR = temp_dir
    yield temp_dir
    service_module.STORAGE_DIR = original_storage
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="function")
def db_session():
    test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    test_db_file.close()
    test_db_url = f"sqlite:///{test_db_file.name}"

    test_engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        yield db, TestingSessionLocal
    finally:
        db.close()
        test_engine.dispose()
        try:
            Path(test_db_file.name).unlink(missing_ok=True)
        except OSError:
            pass

@pytest.fixture(scope="function")
def client(db_session, temp_storage):
    db, session_factory = db_session

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    test_client.session_factory = session_factory
    yield test_client
    app.dependency_overrides.clear()
