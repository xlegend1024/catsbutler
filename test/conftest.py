import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
API_SRC = ROOT / "src" / "api"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from foundry_api import app


@pytest.fixture
def client():
    return TestClient(app)
