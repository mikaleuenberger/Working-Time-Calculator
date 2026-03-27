from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User
from ..security import verify_password


class AuthService:
    def __init__(self, session: Session):
        self._session = session

    def requires_password_setup(self, *, user_id: int, last_name: str) -> User | None:
        """Return user if they match id+last_name and must set/change password."""

        stmt = select(User).where(User.id == user_id)
        user = self._session.execute(stmt).scalar_one_or_none()
        if user is None:
            return None
        if user.last_name.casefold() != last_name.strip().casefold():
            return None
        if bool(user.must_change_password) or (user.password_hash or "") == "":
            return user
        return None

    def authenticate(self, *, user_id: int, last_name: str, password: str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        user = self._session.execute(stmt).scalar_one_or_none()
        if user is None:
            return None
        if user.last_name.casefold() != last_name.strip().casefold():
            return None
        # If a password reset/change is required, block login and guide user to set a new password.
        if bool(user.must_change_password) or (user.password_hash or "") == "":
            return None
        if not verify_password(password or '', user.password_hash or ''):
            return None
        return user
