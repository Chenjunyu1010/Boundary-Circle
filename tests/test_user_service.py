from sqlalchemy.exc import IntegrityError

from src.models.core import UserCreate
from src.services.users import create_user_account


class _ExecResult:
    def first(self):
        return None


class _SessionWithIntegrityError:
    def __init__(self, error: IntegrityError):
        self.error = error
        self.rollback_called = False

    def exec(self, statement):
        return _ExecResult()

    def add(self, user):
        self.user = user

    def commit(self):
        raise self.error

    def rollback(self):
        self.rollback_called = True

    def refresh(self, user):
        raise AssertionError("refresh should not be called after failed commit")


def test_create_user_account_maps_email_integrity_error_to_http_400():
    session = _SessionWithIntegrityError(
        IntegrityError(
            statement="INSERT INTO user ...",
            params={},
            orig=Exception("UNIQUE constraint failed: user.email"),
        )
    )

    try:
        create_user_account(
            session,
            UserCreate(
                username="serviceuser",
                email="service@example.com",
                password="secret123",
            ),
        )
    except Exception as error:
        assert getattr(error, "status_code", None) == 400
        assert getattr(error, "detail", None) == "Email already registered"
    else:
        raise AssertionError("Expected create_user_account to raise HTTPException")

    assert session.rollback_called is True
