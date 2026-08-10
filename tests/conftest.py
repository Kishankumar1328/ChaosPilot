import pytest
import asyncio
import uvicorn
import multiprocessing
from tests.mock_app.app import mock_app

def run_mock_server(host: str, port: int):
    uvicorn.run(mock_app, host=host, port=port, log_level="warning")

@pytest.fixture(scope="session")
def mock_server_url():
    host = "127.0.0.1"
    port = 8888
    proc = multiprocessing.Process(target=run_mock_server, args=(host, port), daemon=True)
    proc.start()
    import time
    time.sleep(1.5)  # Wait for server startup
    yield f"http://{host}:{port}"
    proc.terminate()
