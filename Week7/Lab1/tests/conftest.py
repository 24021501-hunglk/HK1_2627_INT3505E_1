import pytest

from sqlalchemy import event

from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False


@pytest.fixture
def app():
    app = create_app(TestConfig)

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def query_counter(app):
    """Đếm các câu SELECT được thực thi trong quá trình kiểm thử."""
    statements = []

    with app.app_context():
        engine = db.engine

        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)

        event.listen(engine, "before_cursor_execute", before_cursor_execute)

        yield statements

        event.remove(
            engine,
            "before_cursor_execute",
            before_cursor_execute
        )