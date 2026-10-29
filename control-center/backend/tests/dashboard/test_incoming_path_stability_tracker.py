"""Contract for observed incoming path availability transitions."""

from app.dashboard.services.incoming_path_stability_tracker import (
    IncomingPathStabilityTracker,
)


def test_initial_available_observation_is_baseline():
    tracker = IncomingPathStabilityTracker()

    result = tracker.observe(
        path_name="impact",
        available=True,
    )

    assert result.interruptions == 0
    assert result.recoveries == 0


def test_available_to_unavailable_counts_interruption():
    tracker = IncomingPathStabilityTracker()

    tracker.observe(path_name="impact", available=True)

    result = tracker.observe(
        path_name="impact",
        available=False,
    )

    assert result.interruptions == 1
    assert result.recoveries == 0


def test_unavailable_to_available_counts_recovery():
    tracker = IncomingPathStabilityTracker()

    tracker.observe(path_name="impact", available=False)

    result = tracker.observe(
        path_name="impact",
        available=True,
    )

    assert result.interruptions == 0
    assert result.recoveries == 1


def test_repeated_state_does_not_increment():
    tracker = IncomingPathStabilityTracker()

    tracker.observe(path_name="impact", available=True)
    tracker.observe(path_name="impact", available=True)

    result = tracker.observe(
        path_name="impact",
        available=True,
    )

    assert result.interruptions == 0
    assert result.recoveries == 0


def test_unknown_observation_does_not_create_transition():
    tracker = IncomingPathStabilityTracker()

    tracker.observe(path_name="impact", available=True)
    tracker.observe(path_name="impact", available=None)

    result = tracker.observe(
        path_name="impact",
        available=False,
    )

    assert result.interruptions == 1
    assert result.recoveries == 0


def test_paths_have_independent_counters():
    tracker = IncomingPathStabilityTracker()

    tracker.observe(path_name="impact", available=True)
    tracker.observe(path_name="ejtv", available=True)

    tracker.observe(path_name="impact", available=False)

    impact = tracker.observe(
        path_name="impact",
        available=False,
    )

    ejtv = tracker.observe(
        path_name="ejtv",
        available=True,
    )

    assert impact.interruptions == 1
    assert ejtv.interruptions == 0


def test_unknown_initial_state_is_not_interruption():
    tracker = IncomingPathStabilityTracker()

    tracker.observe(path_name="impact", available=None)

    result = tracker.observe(
        path_name="impact",
        available=False,
    )

    assert result.interruptions == 0
    assert result.recoveries == 0


def test_candidate_copy_does_not_mutate_committed_state():
    from copy import deepcopy

    committed = IncomingPathStabilityTracker()

    committed.observe(
        path_name="impact",
        available=True,
    )

    candidate = deepcopy(committed)

    candidate_result = candidate.observe(
        path_name="impact",
        available=False,
    )

    committed_result = committed.observe(
        path_name="impact",
        available=True,
    )

    assert candidate_result.interruptions == 1
    assert committed_result.interruptions == 0


def test_candidate_copy_keeps_paths_independent():
    from copy import deepcopy

    committed = IncomingPathStabilityTracker()

    committed.observe(path_name="impact", available=True)
    committed.observe(path_name="ejtv", available=True)

    candidate = deepcopy(committed)

    candidate.observe(path_name="impact", available=False)

    ejtv = candidate.observe(
        path_name="ejtv",
        available=True,
    )

    assert ejtv.interruptions == 0
    assert ejtv.recoveries == 0


def test_unknown_observation_preserves_previous_state():
    tracker = IncomingPathStabilityTracker()

    tracker.observe(path_name="impact", available=False)
    tracker.observe(path_name="impact", available=None)

    result = tracker.observe(
        path_name="impact",
        available=True,
    )

    assert result.interruptions == 0
    assert result.recoveries == 1


def test_repeated_unavailable_observation_counts_once():
    tracker = IncomingPathStabilityTracker()

    tracker.observe(path_name="impact", available=True)

    tracker.observe(path_name="impact", available=False)
    tracker.observe(path_name="impact", available=False)

    result = tracker.observe(
        path_name="impact",
        available=False,
    )

    assert result.interruptions == 1
    assert result.recoveries == 0
