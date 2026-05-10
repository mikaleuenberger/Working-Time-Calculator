from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User
from ..security import hash_password, validate_password_policy
from ..data_access.seed import seed_users


class UserService:
    def __init__(self, session: Session):
        self._session = session

    def list_users(self) -> list[User]:
        return list(self._session.execute(select(User).order_by(User.id)).scalars().all())

    def seed_from_users_json_if_empty(self, users_json_path: Path) -> int:
        created, skipped = seed_users(self._session, users_json_path)
        # commit will be handled by the session scope in main2.py
        return created

    def set_password(self, *, user_id: int, password: str) -> bool:
        if not validate_password_policy(password):
            return False
        user = self._session.get(User, user_id)
        if user is None:
            return False
        user.password_hash = hash_password(password)
        user.must_change_password = False
        return True

    def create_user(
        self,
        *,
        user_id: int,
        first_name: str,
        last_name: str,
        email: str = "",
        business_role: str = "Mitarbeiter",
        age: int = 18,
    ) -> bool:
        try:
            user_id = int(user_id)
        except Exception:
            return False
        if user_id <= 0:
            return False

        first_name = (first_name or "").strip()
        last_name = (last_name or "").strip()
        if not first_name or not last_name:
            return False

        email = (email or "").strip()
        business_role = (
            business_role or "Mitarbeiter").strip() or "Mitarbeiter"
        try:
            age = int(age)
        except Exception:
            return False
        if age < 0:
            return False

        if self._session.get(User, user_id) is not None:
            return False

        user = User(
            id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            business_role=business_role,
            age=age,
            password_hash="",
            must_change_password=True,
        )
        self._session.add(user)
        return True

    def update_user(
        self,
        *,
        user_id: int,
        first_name: str,
        last_name: str,
        email: str = "",
        business_role: str = "Mitarbeiter",
        age: int = 18,
    ) -> bool:
        user = self._session.get(User, int(user_id))
        if user is None:
            return False

        first_name = (first_name or "").strip()
        last_name = (last_name or "").strip()
        if not first_name or not last_name:
            return False

        email = (email or "").strip()
        business_role = (
            business_role or "Mitarbeiter").strip() or "Mitarbeiter"
        try:
            age = int(age)
        except Exception:
            return False
        if age < 0:
            return False

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.business_role = business_role
        user.age = age
        return True

    def reset_password(self, *, user_id: int) -> bool:
        user = self._session.get(User, int(user_id))
        if user is None:
            return False
        user.password_hash = ""
        user.must_change_password = True
        return True
