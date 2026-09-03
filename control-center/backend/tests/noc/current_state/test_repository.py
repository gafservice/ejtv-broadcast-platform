from app.noc.current_state.repository import (
    NodeHealthDiagnosticRepository,
)


class CompatibleRepository:
    def save(
        self,
        *,
        node_id,
        instance_id,
        diagnostic,
    ) -> None:
        pass

    def latest(
        self,
        *,
        node_id,
        instance_id,
    ):
        return None


class IncompleteRepository:
    def save(
        self,
        *,
        node_id,
        instance_id,
        diagnostic,
    ) -> None:
        pass


def test_compatible_repository_satisfies_runtime_protocol() -> None:
    repository = CompatibleRepository()

    assert isinstance(
        repository,
        NodeHealthDiagnosticRepository,
    )


def test_incomplete_repository_does_not_satisfy_runtime_protocol() -> None:
    repository = IncompleteRepository()

    assert not isinstance(
        repository,
        NodeHealthDiagnosticRepository,
    )
