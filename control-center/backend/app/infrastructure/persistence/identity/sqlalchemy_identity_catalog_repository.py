"""SQLAlchemy persistence for the canonical Identity catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import (
    Session,
    selectinload,
    sessionmaker,
)

from app.domain.identity.entities import Permission, Role
from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
)
from app.infrastructure.persistence.identity.models import (
    PermissionModel,
    RoleModel,
)


class SQLAlchemyIdentityCatalogRepository:
    """Persist and synchronize canonical roles and permissions."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        if not isinstance(session_factory, sessionmaker):
            raise TypeError(
                "session_factory must be a SQLAlchemy sessionmaker"
            )

        self._session_factory = session_factory

    def get_role(
        self,
        role_name: RoleName,
    ) -> Role | None:
        """Return a persisted role by name."""

        if not isinstance(role_name, RoleName):
            raise TypeError("role_name must be a RoleName")

        with self._session_factory() as session:
            model = session.scalar(
                self._role_query().where(
                    RoleModel.name == role_name.value
                )
            )

            if model is None:
                return None

            return self._to_domain(model)

    def list_roles(self) -> tuple[Role, ...]:
        """Return all persisted roles ordered by name."""

        with self._session_factory() as session:
            models = session.scalars(
                self._role_query().order_by(RoleModel.name)
            ).all()

            return tuple(
                self._to_domain(model)
                for model in models
            )

    def save_role(
        self,
        role: Role,
    ) -> None:
        """Create or synchronize a role and its permissions."""

        if not isinstance(role, Role):
            raise TypeError("role must be a Role")

        with self._session_factory() as session:
            try:
                role_model = session.get(
                    RoleModel,
                    role.name.value,
                    options=(
                        selectinload(RoleModel.permissions),
                    ),
                )

                if role_model is None:
                    role_model = RoleModel(
                        name=role.name.value
                    )
                    session.add(role_model)

                role_model.permissions = [
                    self._get_or_create_permission(
                        session=session,
                        permission=permission,
                    )
                    for permission in sorted(
                        role.permissions,
                        key=lambda item: item.name.value,
                    )
                ]

                session.commit()
            except Exception:
                session.rollback()
                raise

    @staticmethod
    def _get_or_create_permission(
        *,
        session: Session,
        permission: Permission,
    ) -> PermissionModel:
        model = session.get(
            PermissionModel,
            permission.name.value,
        )

        if model is None:
            model = PermissionModel(
                name=permission.name.value
            )
            session.add(model)

        return model

    @staticmethod
    def _role_query():
        return select(RoleModel).options(
            selectinload(RoleModel.permissions)
        )

    @staticmethod
    def _to_domain(
        model: RoleModel,
    ) -> Role:
        return Role(
            name=RoleName(model.name),
            permissions=frozenset(
                Permission(
                    name=PermissionName(
                        permission.name
                    )
                )
                for permission in model.permissions
            ),
        )
