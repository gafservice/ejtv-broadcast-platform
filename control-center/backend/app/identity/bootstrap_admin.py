"""Command-line entry point for bootstrapping Identity."""

from __future__ import annotations

import sys

from app.core.config import Settings, get_settings
from app.infrastructure.persistence.audit.sqlalchemy_audit_repository import (
    SQLAlchemyAuditRepository,
)
from app.infrastructure.persistence.database import create_session_factory
from app.infrastructure.persistence.identity.database_initializer import (
    initialize_identity_database,
)
from app.infrastructure.persistence.identity import (
    SQLAlchemyIdentityCatalogRepository,
    SQLAlchemyUserRepository,
)
from app.infrastructure.security.bcrypt_password_hasher import (
    BcryptPasswordHasher,
)
from app.services.identity_bootstrap_service import (
    BootstrapStatus,
    IdentityBootstrapService,
)


def build_bootstrap_service(
    settings: Settings,
) -> IdentityBootstrapService:
    """Build the bootstrap service with production infrastructure."""

    engine = initialize_identity_database(
        settings.identity_database_url,
        echo=False,
    )

    session_factory = create_session_factory(engine)

    return IdentityBootstrapService(
        user_repository=SQLAlchemyUserRepository(
            session_factory
        ),
        password_hasher=BcryptPasswordHasher(
            rounds=settings.bcrypt_rounds
        ),
        audit_repository=SQLAlchemyAuditRepository(
            session_factory
        ),
        catalog_repository=SQLAlchemyIdentityCatalogRepository(
            session_factory
        ),
    )


def run() -> int:
    """Execute the administrator bootstrap."""

    settings = get_settings()
    password = settings.bootstrap_admin_password

    if password is None or not password.strip():
        print(
            "ERROR: BOOTSTRAP_ADMIN_PASSWORD is not configured.",
            file=sys.stderr,
        )
        print(
            "Define it in the .env file before running the bootstrap.",
            file=sys.stderr,
        )
        return 1

    try:
        service = build_bootstrap_service(settings)

        catalog_result = service.synchronize_catalog()

        print(
            "Identity catalog synchronized: "
            f"created={len(catalog_result.created)}, "
            f"updated={len(catalog_result.updated)}, "
            f"unchanged={len(catalog_result.unchanged)}."
        )

        integrity_result = service.verify_integrity()

        if not integrity_result.valid:
            raise RuntimeError(
                "Identity catalog integrity verification failed: "
                f"missing={integrity_result.missing_roles}, "
                f"unexpected={integrity_result.unexpected_roles}, "
                f"mismatched={integrity_result.mismatched_roles}"
            )

        print("Identity catalog integrity verified.")

        result = service.bootstrap_administrator(
            username=settings.bootstrap_admin_username,
            email=settings.bootstrap_admin_email,
            password=password,
        )
    except Exception as error:
        print(
            f"ERROR: Identity bootstrap failed: {error}",
            file=sys.stderr,
        )
        return 1

    if result.status is BootstrapStatus.CREATED:
        print("Identity bootstrap completed successfully.")
        print(
            f"Administrator created: {result.user.username.value}"
        )
        print(f"Email: {result.user.email.value}")
        print(
            "Security notice: remove BOOTSTRAP_ADMIN_PASSWORD "
            "from .env after validating access."
        )
        return 0

    print("Identity bootstrap completed successfully.")
    print(
        "Administrator already exists: "
        f"{result.user.username.value}"
    )
    print("No changes were required.")

    return 0


def main() -> None:
    """Expose the command exit status."""

    raise SystemExit(run())


if __name__ == "__main__":
    main()
