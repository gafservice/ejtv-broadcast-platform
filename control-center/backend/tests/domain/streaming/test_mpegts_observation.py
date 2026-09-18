from dataclasses import FrozenInstanceError

import pytest

from app.domain.streaming.media_observation import (
    ContainerObservation,
    EvidenceAvailability,
    MPEGTSObservation,
    MPEGTSProgramObservation,
    MPEGTSStreamObservation,
)


def make_stream(**overrides) -> MPEGTSStreamObservation:
    values = {
        "pid": 0x0103,
        "stream_type": 0x24,
    }
    values.update(overrides)
    return MPEGTSStreamObservation(**values)


def make_program(**overrides) -> MPEGTSProgramObservation:
    values = {
        "program_number": 1,
        "pmt_pid": 0x0100,
        "pcr_pid": 0x002D,
        "streams": (
            MPEGTSStreamObservation(
                pid=0x0104,
                stream_type=0x0F,
            ),
            MPEGTSStreamObservation(
                pid=0x0103,
                stream_type=0x24,
            ),
        ),
    }
    values.update(overrides)
    return MPEGTSProgramObservation(**values)


def make_mpegts(**overrides) -> MPEGTSObservation:
    values = {
        "availability": EvidenceAvailability.AVAILABLE,
        "transport_stream_id": 1,
        "pat_present": True,
        "pat_version": 0,
        "pmt_present": True,
        "pmt_version": 0,
        "transport_packet_count": 15610,
        "sync_error_count": 0,
        "malformed_packet_count": 0,
        "transport_error_indicator_count": 0,
        "continuity_check_count": 15461,
        "continuity_error_count": 0,
        "discontinuity_indicator_count": 0,
        "programs": (make_program(),),
    }
    values.update(overrides)
    return MPEGTSObservation(**values)


def test_mpegts_stream_preserves_observed_pid_and_stream_type() -> None:
    stream = make_stream()

    assert stream.pid == 0x0103
    assert stream.stream_type == 0x24


@pytest.mark.parametrize("pid", [-1, 0x2000])
def test_mpegts_stream_rejects_invalid_pid(pid: int) -> None:
    with pytest.raises(ValueError):
        make_stream(pid=pid)


def test_mpegts_program_represents_topology_without_hard_coding() -> None:
    program = MPEGTSProgramObservation(
        program_number=7,
        pmt_pid=0x0200,
        pcr_pid=0x0030,
        streams=(
            MPEGTSStreamObservation(
                pid=0x0201,
                stream_type=0x1B,
            ),
        ),
    )

    assert program.program_number == 7
    assert program.pmt_pid == 0x0200
    assert program.pcr_pid == 0x0030
    assert program.streams[0].pid == 0x0201


@pytest.mark.parametrize("pid", [-1, 0x2000])
def test_mpegts_program_rejects_invalid_pmt_pid(pid: int) -> None:
    with pytest.raises(ValueError):
        make_program(pmt_pid=pid)


@pytest.mark.parametrize("pid", [-1, 0x2000])
def test_mpegts_program_rejects_invalid_pcr_pid(pid: int) -> None:
    with pytest.raises(ValueError):
        make_program(pcr_pid=pid)


def test_mpegts_observation_preserves_structural_evidence() -> None:
    observation = make_mpegts()

    assert observation.transport_stream_id == 1
    assert observation.pat_present is True
    assert observation.pat_version == 0
    assert observation.pmt_present is True
    assert observation.pmt_version == 0
    assert len(observation.programs) == 1

    program = observation.programs[0]

    assert program.program_number == 1
    assert program.pmt_pid == 0x0100
    assert program.pcr_pid == 0x002D

    assert {
        (stream.pid, stream.stream_type)
        for stream in program.streams
    } == {
        (0x0104, 0x0F),
        (0x0103, 0x24),
    }


def test_mpegts_observation_preserves_integrity_evidence() -> None:
    observation = make_mpegts()

    assert observation.transport_packet_count == 15610
    assert observation.sync_error_count == 0
    assert observation.malformed_packet_count == 0
    assert observation.transport_error_indicator_count == 0
    assert observation.continuity_check_count == 15461
    assert observation.continuity_error_count == 0
    assert observation.discontinuity_indicator_count == 0


@pytest.mark.parametrize(
    "field_name",
    [
        "transport_packet_count",
        "sync_error_count",
        "malformed_packet_count",
        "transport_error_indicator_count",
        "continuity_check_count",
        "continuity_error_count",
        "discontinuity_indicator_count",
    ],
)
def test_mpegts_observation_rejects_negative_counters(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        make_mpegts(**{field_name: -1})


def test_continuity_errors_cannot_exceed_checks() -> None:
    with pytest.raises(ValueError):
        make_mpegts(
            continuity_check_count=3,
            continuity_error_count=4,
        )


def test_mpegts_observation_does_not_create_health_state() -> None:
    observation = make_mpegts(
        sync_error_count=2,
        continuity_error_count=3,
    )

    assert observation.sync_error_count == 2
    assert observation.continuity_error_count == 3

    assert not hasattr(observation, "health")
    assert not hasattr(observation, "status")


def test_container_can_carry_mpegts_specialization() -> None:
    mpegts = make_mpegts()

    container = ContainerObservation(
        availability=EvidenceAvailability.AVAILABLE,
        container_type="mpegts",
        mpegts=mpegts,
    )

    assert container.mpegts is mpegts
    assert container.container_type == "mpegts"


def test_non_mpegts_container_can_omit_mpegts_specialization() -> None:
    container = ContainerObservation(
        availability=EvidenceAvailability.AVAILABLE,
        container_type="other",
        mpegts=None,
    )

    assert container.mpegts is None


def test_mpegts_domain_objects_are_immutable() -> None:
    observation = make_mpegts()

    with pytest.raises(FrozenInstanceError):
        observation.sync_error_count = 10
