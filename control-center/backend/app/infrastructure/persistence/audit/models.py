"""SQLAlchemy models for identity and access audit records."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class AuditLogModel(Base):
    """Persisted snapshot of an identity or access security event."""

    __tablename__ = "identity_audit_log"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    roles_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    permissions_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    details_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
