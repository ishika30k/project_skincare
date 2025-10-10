import pytest
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app  

from unittest.mock import MagicMock

@pytest.fixture
def mock_db(mocker):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_cursor.execute.return_value = True

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mocker.patch("app.mysql.connection", mock_conn)
    return mock_conn, mock_cursor


@pytest.fixture()
def app():
    flask_app.config.update({
        "TESTING": True,
    })
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()