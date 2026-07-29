from app.domain.identity.entities import AuthenticatedIdentity
from app.domain.identity.exceptions import PermissionDenied
from app.domain.identity.protocols import AuditRepository
from app.domain.identity.value_objects import PermissionName


class AuthorizationService:
    def __init__(
        self,
        *,
        audit_repository: AuditRepository,
    ) -> None:
        self._audit_repository = audit_repository

    def authorize(
        self,
        *,
        identity: AuthenticatedIdentity,
        permission: str,
    ) -> None:
        permission_name = PermissionName(permission)

        if not identity.has_permission(permission_name):
            self._audit_repository.record(
                "identity.authorization.denied",
                identity,
                {
                    "permission": permission,
                },
            )
            raise PermissionDenied

        self._audit_repository.record(
            "identity.authorization.succeeded",
            identity,
            {
                "permission": permission,
            },
        )