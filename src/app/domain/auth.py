from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime


class AuthPrincipalType(enum.StrEnum):
    ADMIN = "admin"
    STUDENT = "student"


@dataclass(slots=True, frozen=True)
class AuthPrincipal:
    id: uuid.UUID
    principal_type: AuthPrincipalType
    username: str
    display_name: str
    is_active: bool


@dataclass(slots=True, frozen=True)
class AuthSession:
    session_id: uuid.UUID
    principal: AuthPrincipal
    created_at: datetime
    expires_at: datetime | None

