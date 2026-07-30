"""SQLAlchemy implementation of the identity user repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import (
    Session,
    selectinload,
    sessionmaker,
)

from app.domain.identity.entities import (
    Permission,
    Role,
    User,
)
from app.domain.identity.value_objects import (
    UserId,
    Username,
)
from app.infrastructure.persistence.identity.mappers import (
    user_model_to_domain,
)
from app.infrastructure.persistence.identity.models import (
    PermissionModel,
    RoleModel,
    UserModel,
)


class SQLAlchemyUserRepository:
    """
    Persist identity users using SQLAlchemy.

    The repository owns ORM graph construction and synchronization.
    Domain entities remain independent from SQLAlchemy.
    """

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        if not isinstance(session_factory, sessionmaker):
            raise TypeError(
                "session_factory must be a SQLAlchemy sessionmaker"
            )

        self._session_factory = session_factory

    def get_by_id(
        self,
        user_id: UserId,
    ) -> User | None:
        """Return the user identified by ``user_id``."""
        if not isinstance(user_id, UserId):
            raise TypeError("user_id must be a UserId")

        with self._session_factory() as session:
            model = session.scalar(
                self._user_query().where(
                    UserModel.id == str(user_id)
                )
            )

            if model is None:
                return None

            return user_model_to_domain(model)

    def get_by_username(
        self,
        username: Username,
    ) -> User | None:
        """Return the user identified by ``username``."""
        if not isinstance(username, Username):
            raise TypeError("username must be a Username")

        with self._session_factory() as session:
            model = session.scalar(
                self._user_query().where(
                    UserModel.username == username.value
                )
            )

            if model is None:
                return None

            return user_model_to_domain(model)

    def save(
        self,
        user: User,
    ) -> None:
        """Insert or update a user and synchronize its assignments."""
        if not isinstance(user, User):
            raise TypeError("user must be a User")

        with self._session_factory() as session:
            try:
                model = self._get_or_create_user(
                    session=session,
                    user=user,
                )

                self._update_scalar_fields(
                    model=model,
                    user=user,
                )

                role_cache: dict[str, RoleModel] = {}
                permission_cache: dict[
                    str,
                    PermissionModel,
                ] = {}

                model.roles = self._synchronize_roles(
                    session=session,
                    roles=user.roles,
                    role_cache=role_cache,
                    permission_cache=permission_cache,
                )

                session.commit()
            except Exception:
                session.rollback()
                raise

    @staticmethod
    def _get_or_create_user(
        *,
        session: Session,
        user: User,
    ) -> UserModel:
        model = session.get(
            UserModel,
            str(user.id),
            options=(
                selectinload(UserModel.roles).selectinload(
                    RoleModel.permissions
                ),
            ),
        )

        if model is None:
            model = UserModel(id=str(user.id))
            session.add(model)

        return model

    @staticmethod
    def _update_scalar_fields(
        *,
        model: UserModel,
        user: User,
    ) -> None:
        model.username = user.username.value
        model.email = user.email.value
        model.password_hash = user.password_hash.value
        model.status = user.status.value

    @classmethod
    def _synchronize_roles(
        cls,
        *,
        session: Session,
        roles: frozenset[Role],
        role_cache: dict[str, RoleModel],
        permission_cache: dict[str, PermissionModel],
    ) -> list[RoleModel]:
        synchronized_roles: list[RoleModel] = []

        for role in sorted(
            roles,
            key=lambda item: item.name.value,
        ):
            role_model = cls._get_or_create_role(
                session=session,
                role=role,
                role_cache=role_cache,
            )

            role_model.permissions = (
                cls._synchronize_permissions(
                    session=session,
                    permissions=role.permissions,
                    permission_cache=permission_cache,
                )
            )

            synchronized_roles.append(role_model)

        return synchronized_roles

    @staticmethod
    def _get_or_create_role(
        *,
        session: Session,
        role: Role,
        role_cache: dict[str, RoleModel],
    ) -> RoleModel:
        role_name = role.name.value

        cached_role = role_cache.get(role_name)

        if cached_role is not None:
            return cached_role

        role_model = session.get(
            RoleModel,
            role_name,
            options=(
                selectinload(RoleModel.permissions),
            ),
        )

        if role_model is None:
            role_model = RoleModel(name=role_name)
            session.add(role_model)

        role_cache[role_name] = role_model

        return role_model

    @classmethod
    def _synchronize_permissions(
        cls,
        *,
        session: Session,
        permissions: frozenset[Permission],
        permission_cache: dict[str, PermissionModel],
    ) -> list[PermissionModel]:
        return [
            cls._get_or_create_permission(
                session=session,
                permission=permission,
                permission_cache=permission_cache,
            )
            for permission in sorted(
                permissions,
                key=lambda item: item.name.value,
            )
        ]

    @staticmethod
    def _get_or_create_permission(
        *,
        session: Session,
        permission: Permission,
        permission_cache: dict[str, PermissionModel],
    ) -> PermissionModel:
        permission_name = permission.name.value

        cached_permission = permission_cache.get(
            permission_name
        )

        if cached_permission is not None:
            return cached_permission

        permission_model = session.get(
            PermissionModel,
            permission_name,
        )

        if permission_model is None:
            permission_model = PermissionModel(
                name=permission_name
            )
            session.add(permission_model)

        permission_cache[permission_name] = (
            permission_model
        )

        return permission_model

    @staticmethod
    def _user_query():
        return select(UserModel).options(
            selectinload(UserModel.roles).selectinload(
                RoleModel.permissions
            )
        )
