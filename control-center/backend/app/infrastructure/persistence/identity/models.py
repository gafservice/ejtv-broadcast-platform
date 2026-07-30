"""SQLAlchemy models for identity persistence."""

from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


identity_user_roles = Table(
    "identity_user_roles",
    Base.metadata,
    Column(
        "user_id",
        String(36),
        ForeignKey(
            "identity_users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "role_name",
        String(64),
        ForeignKey(
            "identity_roles.name",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


identity_role_permissions = Table(
    "identity_role_permissions",
    Base.metadata,
    Column(
        "role_name",
        String(64),
        ForeignKey(
            "identity_roles.name",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "permission_name",
        String(128),
        ForeignKey(
            "identity_permissions.name",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


class UserModel(Base):
    """Persistent representation of an identity user."""

    __tablename__ = "identity_users"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'disabled', 'locked')",
            name="ck_identity_users_status",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )
    username: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(254),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="active",
    )

    roles: Mapped[list[RoleModel]] = relationship(
        secondary=identity_user_roles,
        back_populates="users",
        lazy="selectin",
    )


class RoleModel(Base):
    """Persistent representation of an identity role."""

    __tablename__ = "identity_roles"

    name: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    users: Mapped[list[UserModel]] = relationship(
        secondary=identity_user_roles,
        back_populates="roles",
    )

    permissions: Mapped[list[PermissionModel]] = relationship(
        secondary=identity_role_permissions,
        back_populates="roles",
        lazy="selectin",
    )


class PermissionModel(Base):
    """Persistent representation of an identity permission."""

    __tablename__ = "identity_permissions"

    name: Mapped[str] = mapped_column(
        String(128),
        primary_key=True,
    )

    roles: Mapped[list[RoleModel]] = relationship(
        secondary=identity_role_permissions,
        back_populates="permissions",
    )
