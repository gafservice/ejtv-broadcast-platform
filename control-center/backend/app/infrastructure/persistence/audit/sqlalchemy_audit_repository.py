"""SQLAlchemy implementation of the identity audit repository."""

from __future__ import annotations

import json
from collections.abc import Mapping

from sqlalchemy.orm import Session, sessionmaker

from app.domain.identity.entities import AuthenticatedIdentity
from app.infrastructure.persistence.audit.models import (
    AuditLogModel,
)


class SQLAlchemyAuditRepository:
    """Persist identity and access audit events using SQLAlchemy."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        if not isinstance(session_factory, sessionmaker):
            raise TypeError(
                "session_factory must be a SQLAlchemy sessionmaker"
            )

        self._session_factory = session_factory

    def record(
        self,
        event_type: str,
        identity: AuthenticatedIdentity | None,
        details: Mapping[str, str] | None = None,
    ) -> None:
        """Persist an identity or access-related audit event."""
        normalized_event_type = self._validate_event_type(
            event_type
        )
        normalized_details = self._validate_details(details)

        if (
            identity is not None
            and not isinstance(identity, AuthenticatedIdentity)
        ):
            raise TypeError(
                "identity must be an AuthenticatedIdentity or None"
            )

        model = AuditLogModel(
            event_type=normalized_event_type,
            user_id=(
                str(identity.user_id)
                if identity is not None
                else None
            ),
            username=(
                identity.username.value
                if identity is not None
                else None
            ),
            roles_json=(
                self._serialize_names(identity.roles)
                if identity is not None
                else None
            ),
            permissions_json=(
                self._serialize_names(identity.permissions)
                if identity is not None
                else None
            ),
            details_json=(
                self._serialize_mapping(normalized_details)
                if normalized_details is not None
                else None
            ),
        )

        with self._session_factory() as session:
            try:
                session.add(model)
                session.commit()
            except Exception:
                session.rollback()
                raise

    @staticmethod
    def _validate_event_type(event_type: str) -> str:
        if not isinstance(event_type, str):
            raise TypeError("event_type must be a string")

        normalized = event_type.strip()

        if not normalized:
            raise ValueError("event_type must not be empty")

        if len(normalized) > 100:
            raise ValueError(
                "event_type must contain at most 100 characters"
            )

        return normalized

    @staticmethod
    def _validate_details(
        details: Mapping[str, str] | None,
    ) -> dict[str, str] | None:
        if details is None:
            return None

        if not isinstance(details, Mapping):
            raise TypeError(
                "details must be a mapping of strings or None"
            )

        normalized: dict[str, str] = {}

        for key, value in details.items():
            if not isinstance(key, str):
                raise TypeError(
                    "detail keys must be strings"
                )

            if not isinstance(value, str):
                raise TypeError(
                    "detail values must be strings"
                )

            normalized[key] = value

        return normalized

    @staticmethod
    def _serialize_names(names: frozenset[object]) -> str:
        values = sorted(
            name.value
            for name in names
        )

        return json.dumps(
            values,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _serialize_mapping(
        values: Mapping[str, str],
    ) -> str:
        return json.dumps(
            dict(values),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
