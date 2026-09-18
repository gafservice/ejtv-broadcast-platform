from dataclasses import FrozenInstanceError

import pytest

from app.domain.streaming.media_observation import (
    EvidenceAvailability,
    MPEGTSProgramObservation,
    MPEGTSStreamObservation,
    PCRObservation,
)


def make_pcr(**overrides) -> PCRObservation:
    values = {
        "availability": EvidenceAvailability.AVAILABLE,
        "pid": 0x002D,
        "sample_count": 145,
        "first_pcr": 100.000,
        "last_pcr": 104.805,
        "pcr_span": 4.805,
        "minimum_delta": 0.033,
        "maximum_delta": 0.034,
        "average_delta": 0.033368,
        "median_delta": 0.033,
    }
    values.update(overrides)
    return PCRObservation(**values)


def make_program(**overrides) -> MPEGTSProgramObservation:
    values = {
        "program_number": 1,
        "pmt_pid": 0x0100,
        "pcr_pid": 0x002D,
        "streams": (
            MPEGTSStreamObservation(
                pid=0x0103,
                stream_type=0x24,
            ),
        ),
        "pcr": None,
    }
    values.update(overrides)
    return MPEGTSProgramObservation(**values)


def test_pcr_observation_preserves_sender_clock_evidence() -> None:
    observation = make_pcr()

    assert observation.availability is EvidenceAvailability.AVAILABLE
    assert observation.pid == 0x002D
    assert observation.sample_count == 145

    assert observation.first_pcr == pytest.approx(100.000)
    assert observation.last_pcr == pytest.approx(104.805)
    assert observation.pcr_span == pytest.approx(4.805)

    assert observation.minimum_delta == pytest.approx(0.033)
    assert observation.maximum_delta == pytest.approx(0.034)
    assert observation.average_delta == pytest.approx(0.033368)
    assert observation.median_delta == pytest.approx(0.033)


@pytest.mark.parametrize("pid", [-1, 0x2000])
def test_pcr_observation_rejects_invalid_pid(pid: int) -> None:
    with pytest.raises(ValueError):
        make_pcr(pid=pid)


@pytest.mark.parametrize(
    "field_name",
    [
        "sample_count",
        "first_pcr",
        "last_pcr",
        "pcr_span",
        "minimum_delta",
        "maximum_delta",
        "average_delta",
        "median_delta",
    ],
)
def test_pcr_observation_rejects_negative_values(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        make_pcr(**{field_name: -1})


def test_pcr_delta_statistics_must_be_ordered() -> None:
    with pytest.raises(ValueError):
        make_pcr(
            minimum_delta=0.040,
            maximum_delta=0.030,
        )


def test_pcr_average_delta_must_be_inside_observed_range() -> None:
    with pytest.raises(ValueError):
        make_pcr(
            minimum_delta=0.033,
            maximum_delta=0.034,
            average_delta=0.040,
        )


def test_pcr_median_delta_must_be_inside_observed_range() -> None:
    with pytest.raises(ValueError):
        make_pcr(
            minimum_delta=0.033,
            maximum_delta=0.034,
            median_delta=0.040,
        )


def test_pcr_observation_does_not_assume_last_pcr_after_first_pcr() -> None:
    observation = make_pcr(
        first_pcr=100.0,
        last_pcr=1.0,
        pcr_span=2.0,
    )

    assert observation.first_pcr == pytest.approx(100.0)
    assert observation.last_pcr == pytest.approx(1.0)


def test_pcr_observation_has_no_local_arrival_metrics() -> None:
    observation = make_pcr()

    assert not hasattr(observation, "arrival_span")
    assert not hasattr(observation, "minimum_arrival_gap")
    assert not hasattr(observation, "maximum_arrival_gap")
    assert not hasattr(observation, "average_arrival_gap")
    assert not hasattr(observation, "median_arrival_gap")
    assert not hasattr(observation, "span_difference")


def test_pcr_observation_has_no_health_state() -> None:
    observation = make_pcr()

    assert not hasattr(observation, "health")
    assert not hasattr(observation, "status")


def test_program_can_carry_pcr_observation() -> None:
    pcr = make_pcr()
    program = make_program(pcr=pcr)

    assert program.pcr is pcr
    assert program.pcr_pid == pcr.pid


def test_program_can_exist_without_pcr_observation() -> None:
    program = make_program(pcr=None)

    assert program.pcr is None


def test_program_rejects_wrong_pcr_observation_type() -> None:
    with pytest.raises(TypeError):
        make_program(pcr="not-pcr")


def test_pcr_observation_is_immutable() -> None:
    observation = make_pcr()

    with pytest.raises(FrozenInstanceError):
        observation.sample_count = 999
