"""Immutable navigation selection for INCOMING media paths."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class IncomingSelectionState:
    """Track the selected incoming path independently of telemetry."""

    selected_path_name: str | None = None

    def __post_init__(self) -> None:
        value = self.selected_path_name

        if value is None:
            return

        if not isinstance(value, str):
            raise TypeError(
                "selected_path_name must be a string or None"
            )

        if not value:
            raise ValueError(
                "selected_path_name must not be empty"
            )

    @staticmethod
    def _validate_paths(
        path_names: tuple[str, ...],
    ) -> None:
        if not isinstance(path_names, tuple):
            raise TypeError("path_names must be a tuple")

        for path_name in path_names:
            if not isinstance(path_name, str):
                raise TypeError(
                    "each path_name must be a string"
                )

            if not path_name:
                raise ValueError(
                    "path_name must not be empty"
                )

    def reconcile(
        self,
        path_names: tuple[str, ...],
    ) -> "IncomingSelectionState":
        """Keep a valid identity or select the first available path."""

        self._validate_paths(path_names)

        if not path_names:
            selected = None

        elif self.selected_path_name in path_names:
            selected = self.selected_path_name

        else:
            selected = path_names[0]

        return replace(
            self,
            selected_path_name=selected,
        )

    def move(
        self,
        delta: int,
        path_names: tuple[str, ...],
    ) -> "IncomingSelectionState":
        """Move relative to the current incoming presentation order."""

        self._validate_paths(path_names)

        if isinstance(delta, bool) or not isinstance(delta, int):
            raise TypeError("delta must be an integer")

        current = self.reconcile(path_names)

        if current.selected_path_name is None:
            return current

        index = path_names.index(
            current.selected_path_name
        )

        next_index = min(
            max(index + delta, 0),
            len(path_names) - 1,
        )

        return replace(
            current,
            selected_path_name=path_names[next_index],
        )

    def home(
        self,
        path_names: tuple[str, ...],
    ) -> "IncomingSelectionState":
        """Select the first available incoming path."""

        self._validate_paths(path_names)

        return replace(
            self,
            selected_path_name=(
                path_names[0] if path_names else None
            ),
        )

    def end(
        self,
        path_names: tuple[str, ...],
    ) -> "IncomingSelectionState":
        """Select the last available incoming path."""

        self._validate_paths(path_names)

        return replace(
            self,
            selected_path_name=(
                path_names[-1] if path_names else None
            ),
        )
