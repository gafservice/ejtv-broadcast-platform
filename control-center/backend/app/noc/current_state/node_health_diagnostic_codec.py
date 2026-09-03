"""JSON codec for shared NodeHealthDiagnostic current state.

ENG-013B — Current State

The codec provides an explicit, deterministic representation of the
latest Node health diagnostic stored in shared current-state storage.

It does not define persistence, history, evidence or runtime ownership.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.noc.domain.network_interface_health import (
    NetworkInterfaceHealth,
)
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_health_diagnostic import (
    NodeHealthDiagnostic,
)


class NodeHealthDiagnosticCodec:
    """Encode and decode NodeHealthDiagnostic values as JSON."""

    @staticmethod
    def encode(
        diagnostic: NodeHealthDiagnostic,
    ) -> str:
        if not isinstance(
            diagnostic,
            NodeHealthDiagnostic,
        ):
            raise TypeError(
                "diagnostic must be a NodeHealthDiagnostic"
            )

        payload = {
            "captured_at": diagnostic.captured_at.isoformat(
                timespec="microseconds"
            ),
            "health": diagnostic.health.state.value,
            "system_health": (
                diagnostic.system_health.state.value
            ),
            "network_health": (
                diagnostic.network_health.state.value
            ),
            "network_interfaces": [
                {
                    "interface": interface.interface,
                    "state": interface.state.value,
                    "observed_at": (
                        interface.observed_at.isoformat(
                            timespec="microseconds"
                        )
                    ),
                    "reason": interface.reason,
                    "carrier_ok": interface.carrier_ok,
                    "traffic_ok": interface.traffic_ok,
                    "error_rate": interface.error_rate,
                    "drop_rate": interface.drop_rate,
                }
                for interface in diagnostic.network_interfaces
            ],
        }

        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def decode(
        payload: str,
    ) -> NodeHealthDiagnostic:
        if not isinstance(payload, str):
            raise TypeError(
                "payload must be a string"
            )

        raw: Any = json.loads(payload)

        if not isinstance(raw, dict):
            raise ValueError(
                "NodeHealthDiagnostic payload must be an object"
            )

        interfaces_raw = raw["network_interfaces"]

        if not isinstance(interfaces_raw, list):
            raise ValueError(
                "network_interfaces must be a list"
            )

        interfaces = tuple(
            NodeHealthDiagnosticCodec._decode_interface(
                item
            )
            for item in interfaces_raw
        )

        return NodeHealthDiagnostic(
            captured_at=NodeHealthDiagnosticCodec._decode_datetime(
                raw["captured_at"]
            ),
            health=NodeHealth(
                state=NodeHealthState.from_value(
                    raw["health"]
                )
            ),
            system_health=NodeHealth(
                state=NodeHealthState.from_value(
                    raw["system_health"]
                )
            ),
            network_health=NodeHealth(
                state=NodeHealthState.from_value(
                    raw["network_health"]
                )
            ),
            network_interfaces=interfaces,
        )

    @staticmethod
    def _decode_interface(
        raw: Any,
    ) -> NetworkInterfaceHealth:
        if not isinstance(raw, dict):
            raise ValueError(
                "network interface payload must be an object"
            )

        return NetworkInterfaceHealth(
            interface=raw["interface"],
            state=NodeHealthState.from_value(
                raw["state"]
            ),
            observed_at=NodeHealthDiagnosticCodec._decode_datetime(
                raw["observed_at"]
            ),
            reason=raw["reason"],
            carrier_ok=raw["carrier_ok"],
            traffic_ok=raw["traffic_ok"],
            error_rate=raw["error_rate"],
            drop_rate=raw["drop_rate"],
        )

    @staticmethod
    def _decode_datetime(
        value: Any,
    ) -> datetime:
        if not isinstance(value, str):
            raise ValueError(
                "datetime value must be a string"
            )

        return datetime.fromisoformat(value)
