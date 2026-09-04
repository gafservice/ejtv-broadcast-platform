"""Canonical renderer for derived NOC history PDF reports.

ENG-013B — Operational History.

The renderer transforms already-selected durable history records into one
human-readable PDF document. It does not query history repositories, choose
history ranges, publish files, seal evidence, perform retention, or own
runtime lifecycle.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.noc.history.alarm_transition import AlarmTransition
from app.noc.history.event_history_record import EventHistoryRecord
from app.noc.history.evidence_writer import (
    alarm_transition_evidence_payload,
    event_evidence_payload,
)


def render_history_pdf(
    *,
    start: datetime,
    end: datetime,
    events: tuple[EventHistoryRecord, ...],
    alarm_transitions: tuple[AlarmTransition, ...],
    node_id: str | None = None,
    instance_id: str | None = None,
) -> bytes:
    """Render one human-readable NOC history report for [start, end)."""

    normalized_start = _utc_timestamp(
        start,
        name="start",
    )
    normalized_end = _utc_timestamp(
        end,
        name="end",
    )

    if normalized_start >= normalized_end:
        raise ValueError(
            "start must be earlier than end"
        )

    if not isinstance(events, tuple):
        raise TypeError(
            "events must be a tuple"
        )

    if not isinstance(
        alarm_transitions,
        tuple,
    ):
        raise TypeError(
            "alarm_transitions must be a tuple"
        )

    if (
        node_id is not None
        and not isinstance(node_id, str)
    ):
        raise TypeError(
            "node_id must be a str or None"
        )

    if (
        instance_id is not None
        and not isinstance(instance_id, str)
    ):
        raise TypeError(
            "instance_id must be a str or None"
        )

    event_payloads = tuple(
        event_evidence_payload(record)
        for record in events
    )
    alarm_payloads = tuple(
        alarm_transition_evidence_payload(
            transition
        )
        for transition in alarm_transitions
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="NOC Historical Report",
        author="EJTV NOC",
        subject="Derived operational history report",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "NocReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        spaceAfter=8 * mm,
    )

    heading_style = ParagraphStyle(
        "NocReportHeading",
        parent=styles["Heading2"],
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
    )

    body_style = ParagraphStyle(
        "NocReportBody",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
    )

    small_style = ParagraphStyle(
        "NocReportSmall",
        parent=body_style,
        fontSize=7,
        leading=9,
    )

    story = [
        Paragraph(
            "NOC Historical Report",
            title_style,
        ),
        _metadata_table(
            start=normalized_start,
            end=normalized_end,
            node_id=node_id,
            instance_id=instance_id,
            event_count=len(event_payloads),
            alarm_count=len(alarm_payloads),
            body_style=body_style,
        ),
        Spacer(1, 4 * mm),
        Paragraph(
            "Events",
            heading_style,
        ),
    ]

    story.extend(
        _event_section(
            event_payloads,
            body_style=body_style,
            small_style=small_style,
        )
    )

    story.append(
        Paragraph(
            "Alarm transitions",
            heading_style,
        )
    )

    story.extend(
        _alarm_section(
            alarm_payloads,
            body_style=body_style,
            small_style=small_style,
        )
    )

    document.build(story)

    return buffer.getvalue()


def _metadata_table(
    *,
    start: datetime,
    end: datetime,
    node_id: str | None,
    instance_id: str | None,
    event_count: int,
    alarm_count: int,
    body_style: ParagraphStyle,
) -> Table:
    data = [
        [
            Paragraph("<b>Scope</b>", body_style),
            Paragraph(
                _text(
                    (
                        f"Node: {node_id or 'ALL'}; "
                        f"Instance: {instance_id or 'ALL'}"
                    )
                ),
                body_style,
            ),
        ],
        [
            Paragraph("<b>Start UTC</b>", body_style),
            Paragraph(
                _text(_format_timestamp(start)),
                body_style,
            ),
        ],
        [
            Paragraph("<b>End UTC</b>", body_style),
            Paragraph(
                _text(_format_timestamp(end)),
                body_style,
            ),
        ],
        [
            Paragraph("<b>Events</b>", body_style),
            Paragraph(
                str(event_count),
                body_style,
            ),
        ],
        [
            Paragraph(
                "<b>Alarm transitions</b>",
                body_style,
            ),
            Paragraph(
                str(alarm_count),
                body_style,
            ),
        ],
    ]

    table = Table(
        data,
        colWidths=(42 * mm, 138 * mm),
        repeatRows=0,
    )

    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    return table


def _event_section(
    payloads: tuple[dict[str, object], ...],
    *,
    body_style: ParagraphStyle,
    small_style: ParagraphStyle,
) -> list[object]:
    if not payloads:
        return [
            Paragraph(
                "No events in the selected interval.",
                body_style,
            )
        ]

    rows: list[list[object]] = [
        [
            Paragraph("<b>Timestamp</b>", small_style),
            Paragraph("<b>Severity</b>", small_style),
            Paragraph("<b>Event</b>", small_style),
            Paragraph("<b>Details</b>", small_style),
        ]
    ]

    for payload in payloads:
        details = [
            str(payload["title"]),
            str(payload["description"]),
            f"Source: {payload['source']}",
            f"Event ID: {payload['event_id']}",
        ]

        if payload["correlation_id"] is not None:
            details.append(
                f"Correlation: {payload['correlation_id']}"
            )

        if payload["attributes"] is not None:
            details.append(
                "Attributes: "
                + _structured_text(
                    payload["attributes"]
                )
            )

        rows.append(
            [
                Paragraph(
                    _text(str(payload["timestamp"])),
                    small_style,
                ),
                Paragraph(
                    _text(str(payload["severity"])),
                    small_style,
                ),
                Paragraph(
                    _text(str(payload["event_type"])),
                    small_style,
                ),
                Paragraph(
                    "<br/>".join(
                        _text(value)
                        for value in details
                    ),
                    small_style,
                ),
            ]
        )

    table = LongTable(
        rows,
        repeatRows=1,
        colWidths=(
            34 * mm,
            18 * mm,
            35 * mm,
            93 * mm,
        ),
    )

    table.setStyle(
        _history_table_style()
    )

    return [table]


def _alarm_section(
    payloads: tuple[dict[str, object], ...],
    *,
    body_style: ParagraphStyle,
    small_style: ParagraphStyle,
) -> list[object]:
    if not payloads:
        return [
            Paragraph(
                "No alarm transitions in the selected interval.",
                body_style,
            )
        ]

    rows: list[list[object]] = [
        [
            Paragraph("<b>Timestamp</b>", small_style),
            Paragraph("<b>Transition</b>", small_style),
            Paragraph("<b>State</b>", small_style),
            Paragraph("<b>Details</b>", small_style),
        ]
    ]

    for payload in payloads:
        details = [
            f"Alarm ID: {payload['alarm_id']}",
            f"Source: {payload['source']}",
        ]

        if payload["actor"] is not None:
            details.append(
                f"Actor: {payload['actor']}"
            )

        if payload["metadata"] is not None:
            details.append(
                "Metadata: "
                + _structured_text(
                    payload["metadata"]
                )
            )

        rows.append(
            [
                Paragraph(
                    _text(str(payload["timestamp"])),
                    small_style,
                ),
                Paragraph(
                    _text(
                        str(
                            payload[
                                "transition_type"
                            ]
                        )
                    ),
                    small_style,
                ),
                Paragraph(
                    _text(str(payload["state"])),
                    small_style,
                ),
                Paragraph(
                    "<br/>".join(
                        _text(value)
                        for value in details
                    ),
                    small_style,
                ),
            ]
        )

    table = LongTable(
        rows,
        repeatRows=1,
        colWidths=(
            34 * mm,
            32 * mm,
            25 * mm,
            89 * mm,
        ),
    )

    table.setStyle(
        _history_table_style()
    )

    return [table]


def _history_table_style() -> TableStyle:
    return TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )


def _structured_text(
    value: object,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _text(
    value: str,
) -> str:
    return escape(
        value
    ).replace(
        "\n",
        "<br/>",
    )


def _format_timestamp(
    value: datetime,
) -> str:
    return value.isoformat().replace(
        "+00:00",
        "Z",
    )


def _utc_timestamp(
    value: datetime,
    *,
    name: str,
) -> datetime:
    if not isinstance(
        value,
        datetime,
    ):
        raise TypeError(
            f"{name} must be a datetime"
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(
            f"{name} must be timezone-aware and UTC"
        )

    if value.utcoffset() != timedelta(0):
        raise ValueError(
            f"{name} must be expressed in UTC"
        )

    return value.astimezone(
        timezone.utc
    )
