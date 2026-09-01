from datetime import datetime

from app.noc.history.repository import (
    AlarmHistoryRepository,
    EventHistoryRepository,
)


class FakeEventHistoryRepository:
    def append(self, record) -> None:
        pass

    def get(self, event_id):
        return None

    def list_between(
        self,
        start: datetime,
        end: datetime,
        *,
        node_id=None,
        instance_id=None,
    ):
        return ()


class FakeAlarmHistoryRepository:
    def save_current(
        self,
        *,
        node_id,
        instance_id,
        alarm,
    ) -> None:
        pass

    def append_transition(
        self,
        transition,
    ) -> None:
        pass

    def record_lifecycle(
        self,
        *,
        node_id,
        instance_id,
        alarm,
        transition,
    ) -> None:
        pass

    def get_current(
        self,
        alarm_id,
    ):
        return None

    def list_all(
        self,
        *,
        node_id=None,
        instance_id=None,
    ):
        return ()

    def record_historical_transition(
        self,
        *,
        node_id,
        instance_id,
        transition,
    ) -> None:
        return None

    def list_active(
        self,
        *,
        node_id=None,
        instance_id=None,
    ):
        return ()

    def list_transitions(
        self,
        alarm_id,
    ):
        return ()

    def list_transitions_between(
        self,
        start: datetime,
        end: datetime,
        *,
        node_id=None,
        instance_id=None,
    ):
        return ()


def test_event_repository_protocol_is_runtime_checkable() -> None:
    repository = FakeEventHistoryRepository()

    assert isinstance(
        repository,
        EventHistoryRepository,
    )


def test_alarm_repository_protocol_is_runtime_checkable() -> None:
    repository = FakeAlarmHistoryRepository()

    assert isinstance(
        repository,
        AlarmHistoryRepository,
    )


def test_incomplete_event_repository_does_not_satisfy_contract() -> None:
    class IncompleteRepository:
        def append(self, record) -> None:
            pass

    assert not isinstance(
        IncompleteRepository(),
        EventHistoryRepository,
    )


def test_incomplete_alarm_repository_does_not_satisfy_contract() -> None:
    class IncompleteRepository:
        def save_current(
            self,
            *,
            node_id,
            instance_id,
            alarm,
        ) -> None:
            pass

    assert not isinstance(
        IncompleteRepository(),
        AlarmHistoryRepository,
    )
