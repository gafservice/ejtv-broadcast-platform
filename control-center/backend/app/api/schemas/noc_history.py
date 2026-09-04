"""HTTP schemas for NOC historical exports."""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HistoryCsvExportRequest(BaseModel):
    """Requested UTC interval for one derived CSV history export."""

    model_config = ConfigDict(
        extra="forbid"
    )

    start: datetime = Field(
        description=(
            "Inclusive UTC start of the historical export interval."
        ),
        examples=["2026-09-01T00:00:00Z"],
    )
    end: datetime = Field(
        description=(
            "Exclusive UTC end of the historical export interval."
        ),
        examples=["2026-09-02T00:00:00Z"],
    )

    @model_validator(mode="after")
    def validate_interval(self) -> "HistoryCsvExportRequest":
        """Require one non-empty half-open interval expressed in UTC."""

        for field_name, value in (
            ("start", self.start),
            ("end", self.end),
        ):
            if (
                value.tzinfo is None
                or value.utcoffset() is None
            ):
                raise ValueError(
                    f"{field_name} must be timezone-aware and UTC"
                )

            if value.utcoffset() != timezone.utc.utcoffset(value):
                raise ValueError(
                    f"{field_name} must be timezone-aware and UTC"
                )

        if self.start >= self.end:
            raise ValueError(
                "start must be earlier than end"
            )

        return self
